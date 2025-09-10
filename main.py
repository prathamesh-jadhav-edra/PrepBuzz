"""Main CLI interface for PrepBuzz CAT Questions RAG System."""

import click
import sys
import warnings
from loguru import logger
from src.core import flow_engine, db
from src.flows import *  # Import all flows to register them
from src.utils.config import config

# Suppress MoviePy syntax warnings (cosmetic issues in Python 3.13)
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", message=".*invalid escape sequence.*")
warnings.filterwarnings("ignore", message=".*is.*with.*literal.*")

# Configure logger
logger.remove()
logger.add(sys.stderr, level=config.log_level)
logger.add(config.output_dir + "/logs/prepbuzz_{time}.log", rotation="1 day")


@click.group()
def cli():
    """PrepBuzz - CAT Questions RAG System for generating educational videos."""
    pass


@cli.command()
@click.option(
    "--subject",
    type=click.Choice(["Quant", "Verbal", "Logic", "DI"]),
    help="Subject to filter questions by",
)
@click.option("--count", default=1, help="Number of videos to generate")
def generate(subject, count):
    """Generate educational videos from CAT questions."""
    click.echo(f"🚀 Starting PrepBuzz video generation...")
    click.echo(f"📊 Subject filter: {subject or 'All subjects'}")
    click.echo(f"🎬 Videos to generate: {count}")

    # Check if database has questions
    question_count = db.get_question_count()
    if question_count == 0:
        click.echo("❌ No questions found in database. Please run 'setup' first.")
        return

    click.echo(f"📚 Found {question_count} questions in database")

    # Define processing pipeline
    pipeline = [
        "question_selection",
        "reasoning_extraction",
        "llm_processing",
        "video_generation",
    ]

    successful_generations = 0

    for i in range(count):
        click.echo(f"\n🎯 Generating video {i+1}/{count}...")

        # Initial data
        input_data = {}
        if subject:
            input_data["subject"] = subject

        # Execute pipeline
        try:
            result = flow_engine.execute_pipeline(pipeline, input_data)

            if result.success:
                video_path = result.data.get("video_path")
                click.echo(f"✅ Video generated successfully: {video_path}")
                successful_generations += 1
            else:
                click.echo(f"❌ Video generation failed: {result.error}")

        except Exception as e:
            click.echo(f"❌ Error generating video: {e}")

    # Summary
    click.echo(f"\n📈 Generation Summary:")
    click.echo(f"✅ Successful: {successful_generations}/{count}")
    if successful_generations > 0:
        click.echo(f"📁 Output directory: {config.output_dir}/videos")


@cli.command()
def status():
    """Check system status and configuration."""
    click.echo("🔍 PrepBuzz System Status\n")

    # Database status
    try:
        question_count = db.get_question_count()
        subjects = db.get_subjects()
        click.echo(f"📚 Database: {question_count} questions")
        if subjects:
            click.echo(f"📖 Subjects: {', '.join(subjects)}")
    except Exception as e:
        click.echo(f"❌ Database error: {e}")

    # Qdrant status
    try:
        if db.qdrant_client:
            click.echo("✅ Qdrant: Connected")
        else:
            click.echo("❌ Qdrant: Not available")
    except Exception as e:
        click.echo(f"❌ Qdrant error: {e}")

    # LLM status
    from src.core.llm_factory import LLMFactory

    providers = LLMFactory.get_available_providers()
    click.echo(f"🤖 LLM Providers: {', '.join(providers)}")

    # Check API keys
    if config.has_paid_llm:
        click.echo("💰 Paid LLM: Available")
    else:
        click.echo("🆓 Using free/local LLM")

    # Flows status
    available_flows = flow_engine.registry.get_available_flows()
    click.echo(f"⚙️  Available Flows: {', '.join(available_flows)}")

    # Output directory
    click.echo(f"📁 Output Directory: {config.output_dir}")


@cli.command()
def setup():
    """Setup system with sample CAT questions."""
    click.echo("🔧 Setting up PrepBuzz system...")

    # Create sample questions for testing
    sample_questions = [
        {
            "id": "cat_2023_quant_001",
            "subject": "Quant",
            "year": 2023,
            "question_text": "If log₂(x) + log₂(y) = 5 and log₂(x) - log₂(y) = 1, find the value of xy.",
            "options": ["32", "16", "8", "64"],
            "correct_answer": "A",
            "topic": "Logarithms",
            "difficulty": "Medium",
        },
        {
            "id": "cat_2022_verbal_001",
            "subject": "Verbal",
            "year": 2022,
            "question_text": "The passage discusses the impact of technology on modern education. Which of the following best summarizes the author's main argument?",
            "options": [
                "Technology has completely revolutionized education",
                "Technology offers both benefits and challenges to education",
                "Traditional teaching methods are obsolete",
                "Students prefer digital learning exclusively",
            ],
            "correct_answer": "B",
            "topic": "Reading Comprehension",
            "difficulty": "Medium",
        },
        {
            "id": "cat_2023_logic_001",
            "subject": "Logic",
            "year": 2023,
            "question_text": "In a sequence, every third number is the sum of the previous two numbers. If the first two numbers are 1 and 2, what is the 8th number in the sequence?",
            "options": ["21", "34", "55", "89"],
            "correct_answer": "A",
            "topic": "Sequences",
            "difficulty": "Medium",
        },
    ]

    from src.core.database import CATQuestion

    # Store sample questions
    stored_count = 0
    for q_data in sample_questions:
        question = CATQuestion(
            id=q_data["id"],
            subject=q_data["subject"],
            year=q_data["year"],
            question_text=q_data["question_text"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            topic=q_data["topic"],
            difficulty=q_data["difficulty"],
        )

        if db.store_question(question):
            stored_count += 1

    click.echo(f"✅ Stored {stored_count} sample questions")
    click.echo("🎉 Setup completed! You can now run 'generate' command.")


@cli.command()
def test():
    """Test the complete pipeline with a sample question."""
    click.echo("🧪 Testing complete pipeline...")

    # Check if we have questions
    question_count = db.get_question_count()
    if question_count == 0:
        click.echo("❌ No questions found. Running setup first...")
        # Run setup
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(setup)

    # Test pipeline
    pipeline = [
        "question_selection",
        "reasoning_extraction",
        "llm_processing",
        "video_generation",
    ]

    click.echo("🔄 Testing pipeline flows...")
    result = flow_engine.execute_pipeline(pipeline)

    if result.success:
        click.echo("✅ Pipeline test successful!")
        if "video_path" in result.data:
            click.echo(f"🎬 Test video: {result.data['video_path']}")
    else:
        click.echo(f"❌ Pipeline test failed: {result.error}")

        # Show which flows completed
        if result.metadata and "completed_flows" in result.metadata:
            click.echo("\n📊 Flow Status:")
            for flow_info in result.metadata["completed_flows"]:
                status = "✅" if flow_info["success"] else "❌"
                click.echo(f"  {status} {flow_info['flow']}")
                if flow_info.get("error"):
                    click.echo(f"    Error: {flow_info['error']}")


if __name__ == "__main__":
    cli()
