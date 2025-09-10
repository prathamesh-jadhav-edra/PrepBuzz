"""Database management for CAT questions and vector storage."""

import sqlite3
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http import models

from ..utils.config import config


@dataclass
class CATQuestion:
    """Represents a CAT question with metadata."""
    id: str
    subject: str  # Quant, Verbal, Logic, DI
    year: int
    question_text: str
    options: List[str]
    correct_answer: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None


class DatabaseManager:
    """Manages SQLite and Qdrant database operations."""
    
    def __init__(self):
        """Initialize database connections."""
        self.sqlite_path = config.sqlite_path
        self.qdrant_client = None
        self.collection_name = "cat_questions"
        self._init_sqlite()
        self._init_qdrant()
    
    def _init_sqlite(self) -> None:
        """Initialize SQLite database."""
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    options TEXT NOT NULL,  -- JSON array
                    correct_answer TEXT NOT NULL,
                    topic TEXT,
                    difficulty TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_subject ON questions(subject)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_year ON questions(year)
            """)
            conn.commit()
        
        logger.info(f"SQLite database initialized at {self.sqlite_path}")
    
    def _init_qdrant(self) -> None:
        """Initialize Qdrant vector database."""
        try:
            self.qdrant_client = QdrantClient(
                host=config.qdrant_host,
                port=config.qdrant_port
            )
            
            # Check if collection exists, create if not
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            self.qdrant_client = None
    
    def store_question(self, question: CATQuestion) -> bool:
        """Store a CAT question in SQLite."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO questions 
                    (id, subject, year, question_text, options, correct_answer, topic, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    question.id,
                    question.subject,
                    question.year,
                    question.question_text,
                    json.dumps(question.options),
                    question.correct_answer,
                    question.topic,
                    question.difficulty
                ))
                conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store question {question.id}: {e}")
            return False
    
    def store_question_embedding(self, question_id: str, embedding: List[float]) -> bool:
        """Store question embedding in Qdrant."""
        if not self.qdrant_client:
            logger.error("Qdrant client not available")
            return False
        
        try:
            # Get question metadata from SQLite
            question = self.get_question(question_id)
            if not question:
                logger.error(f"Question {question_id} not found in SQLite")
                return False
            
            # Store in Qdrant with metadata
            point = PointStruct(
                id=question_id,
                vector=embedding,
                payload={
                    "subject": question.subject,
                    "year": question.year,
                    "topic": question.topic,
                    "difficulty": question.difficulty
                }
            )
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding for question {question_id}: {e}")
            return False
    
    def get_question(self, question_id: str) -> Optional[CATQuestion]:
        """Retrieve a question by ID."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM questions WHERE id = ?
                """, (question_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return CATQuestion(
                    id=row["id"],
                    subject=row["subject"],
                    year=row["year"],
                    question_text=row["question_text"],
                    options=json.loads(row["options"]),
                    correct_answer=row["correct_answer"],
                    topic=row["topic"],
                    difficulty=row["difficulty"]
                )
                
        except Exception as e:
            logger.error(f"Failed to get question {question_id}: {e}")
            return None
    
    def get_random_question(self, subject: Optional[str] = None) -> Optional[CATQuestion]:
        """Get a random question, optionally filtered by subject."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if subject:
                    cursor = conn.execute("""
                        SELECT * FROM questions WHERE subject = ? 
                        ORDER BY RANDOM() LIMIT 1
                    """, (subject,))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM questions 
                        ORDER BY RANDOM() LIMIT 1
                    """)
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return CATQuestion(
                    id=row["id"],
                    subject=row["subject"],
                    year=row["year"],
                    question_text=row["question_text"],
                    options=json.loads(row["options"]),
                    correct_answer=row["correct_answer"],
                    topic=row["topic"],
                    difficulty=row["difficulty"]
                )
                
        except Exception as e:
            logger.error(f"Failed to get random question: {e}")
            return None
    
    def search_similar_questions(self, embedding: List[float], limit: int = 5) -> List[Tuple[CATQuestion, float]]:
        """Search for similar questions using vector similarity."""
        if not self.qdrant_client:
            logger.error("Qdrant client not available")
            return []
        
        try:
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                with_payload=True
            )
            
            results = []
            for hit in search_result:
                question = self.get_question(hit.id)
                if question:
                    results.append((question, hit.score))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar questions: {e}")
            return []
    
    def get_question_count(self) -> int:
        """Get total number of questions in database."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM questions")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get question count: {e}")
            return 0
    
    def get_subjects(self) -> List[str]:
        """Get list of available subjects."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.execute("SELECT DISTINCT subject FROM questions")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get subjects: {e}")
            return []


# Global database instance
db = DatabaseManager()