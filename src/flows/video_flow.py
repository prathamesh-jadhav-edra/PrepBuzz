"""Video generation flow for creating slideshow with audio."""

from typing import Dict, Any, List
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip
import tempfile
import os
from datetime import datetime
from ..core.flow_engine import BaseFlow, FlowResult, register_flow
from ..utils.config import config


@register_flow("video_generation")
class VideoGenerationFlow(BaseFlow):
    """Flow for generating video content."""
    
    def __init__(self, name: str, config_dict: Dict[str, Any] = None):
        """Initialize video flow."""
        super().__init__(name, config_dict)
        self.output_dir = Path(config.output_dir) / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(config.output_dir) / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, input_data: Dict[str, Any]) -> FlowResult:
        """Execute video generation."""
        self.log_start()
        
        try:
            # Validate input
            if not self.validate_input(input_data, ["question", "formatted_explanation"]):
                return FlowResult(
                    success=False,
                    data=input_data,
                    error="Missing question or explanation data"
                )
            
            
            question_data = input_data["question"]
            explanation = input_data["formatted_explanation"]
            
            
            # Generate video
            video_path = self._create_video(question_data, explanation)
            
            if not video_path:
                return FlowResult(
                    success=False,
                    data=input_data,
                    error="Video generation failed"
                )
            
            result_data = input_data.copy()
            result_data["video_path"] = str(video_path)
            
            self.logger.info(f"Video generated: {video_path}")
            
            result = FlowResult(
                success=True,
                data=result_data,
                metadata={"flow": "video_generation", "output_file": str(video_path)}
            )
            
            
            self.log_end(result)
            return result
            
        except Exception as e:
            error_msg = f"Video generation failed: {str(e)}"
            self.logger.error(error_msg)
            result = FlowResult(
                success=False,
                data=input_data,
                error=error_msg
            )
            self.log_end(result)
            return result
    
    def _create_video(self, question_data: Dict[str, Any], explanation: str) -> Path:
        """Create video from question and explanation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"cat_question_{timestamp}.mp4"
        video_path = self.output_dir / video_filename
        
        try:
            # Create slides
            slides = self._create_slides(question_data, explanation)
            
            # Generate audio narration
            audio_path = self._generate_audio(explanation)
            
            # Combine slides and audio
            self._combine_slides_and_audio(slides, audio_path, video_path)
            
            # Cleanup temporary files
            self._cleanup_temp_files([audio_path] + slides)
            
            return video_path
            
        except Exception as e:
            self.logger.error(f"Video creation failed: {e}")
            return None
    
    def _create_slides(self, question_data: Dict[str, Any], explanation: str) -> List[Path]:
        """Create slide images."""
        slides = []
        
        # Slide 1: Question
        slide1_path = self._create_question_slide(question_data)
        slides.append(slide1_path)
        
        # Slide 2: Options
        slide2_path = self._create_options_slide(question_data)
        slides.append(slide2_path)
        
        # Slide 3: Explanation
        slide3_path = self._create_explanation_slide(explanation)
        slides.append(slide3_path)
        
        return slides
    
    def _create_question_slide(self, question_data: Dict[str, Any]) -> Path:
        """Create question slide."""
        slide_path = self.temp_dir / f"question_slide_{datetime.now().strftime('%H%M%S')}.png"
        
        # Create image
        img = Image.new('RGB', (1280, 720), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to load a nice font, fallback to default
            font_title = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            font_text = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        # Title
        title = f"CAT {question_data['subject']} Question ({question_data['year']})"
        draw.text((50, 50), title, fill='black', font=font_title)
        
        # Question text
        question_text = question_data['question_text']
        lines = self._wrap_text(question_text, 80)
        
        y_pos = 150
        for line in lines:
            draw.text((50, y_pos), line, fill='black', font=font_text)
            y_pos += 35
        
        img.save(slide_path)
        return slide_path
    
    def _create_options_slide(self, question_data: Dict[str, Any]) -> Path:
        """Create options slide."""
        slide_path = self.temp_dir / f"options_slide_{datetime.now().strftime('%H%M%S')}.png"
        
        img = Image.new('RGB', (1280, 720), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            font_text = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        # Title
        draw.text((50, 50), "Answer Options", fill='black', font=font_title)
        
        # Options
        y_pos = 150
        for i, option in enumerate(question_data['options']):
            option_text = f"{chr(65+i)}. {option}"
            
            # Highlight correct answer
            color = 'green' if chr(65+i) == question_data['correct_answer'] else 'black'
            
            # Wrap long options
            lines = self._wrap_text(option_text, 60)
            for line in lines:
                draw.text((50, y_pos), line, fill=color, font=font_text)
                y_pos += 35
            y_pos += 20  # Extra space between options
        
        img.save(slide_path)
        return slide_path
    
    def _create_explanation_slide(self, explanation: str) -> Path:
        """Create explanation slide."""
        slide_path = self.temp_dir / f"explanation_slide_{datetime.now().strftime('%H%M%S')}.png"
        
        img = Image.new('RGB', (1280, 720), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            font_text = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 22)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        # Title
        draw.text((50, 50), "Solution Explanation", fill='black', font=font_title)
        
        # Clean and format explanation text
        clean_explanation = self._clean_explanation_text(explanation)
        
        # Handle mathematical vs regular content differently
        if '\n' in clean_explanation and ("Step" in clean_explanation or "Equation" in clean_explanation):
            # Mathematical content - split by lines and wrap each individually
            lines = []
            for line in clean_explanation.split('\n'):
                if line.strip():
                    wrapped = self._wrap_text(line, 80)  # Slightly less width for equations
                    lines.extend(wrapped)
        else:
            # Regular content - wrap as before
            lines = self._wrap_text(clean_explanation, 85)
        
        y_pos = 130
        for line in lines[:20]:  # Limit to fit on slide
            draw.text((50, y_pos), line, fill='black', font=font_text)
            y_pos += 28
        
        img.save(slide_path)
        return slide_path
    
    def _clean_explanation_text(self, explanation: str) -> str:
        """Clean explanation text for display while preserving mathematical structure."""
        # Check if this is a formatted mathematical solution
        if "Step" in explanation and ("Equation" in explanation or "Result" in explanation):
            # This is our mathematical solution - preserve structure
            lines = []
            for line in explanation.split('\n'):
                line = line.strip()
                if line:
                    # Remove only excessive markdown but keep structure
                    clean_line = line.replace("**", "").replace("###", "").replace("##", "")
                    clean_line = clean_line.replace("*This solution was generated", "Generated")
                    if clean_line and not clean_line.startswith("---"):
                        lines.append(clean_line)
            return '\n'.join(lines)
        else:
            # Original cleaning for non-mathematical content
            clean_text = explanation.replace("**", "").replace("##", "").replace("#", "")
            clean_text = clean_text.replace("*", "").strip()
            
            # Remove excessive whitespace
            lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
            return ' '.join(lines)
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)  # Word is longer than width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _generate_audio(self, explanation: str) -> Path:
        """Generate audio narration."""
        audio_path = self.temp_dir / f"narration_{datetime.now().strftime('%H%M%S')}.mp3"
        
        try:
            # Create narration text
            narration_text = self._create_narration_text(explanation)
            
            # Generate audio using gTTS
            tts = gTTS(text=narration_text, lang='en', slow=False)
            tts.save(str(audio_path))
            
            return audio_path
            
        except Exception as e:
            self.logger.error(f"Audio generation failed: {e}")
            # Create silent audio fallback
            return self._create_silent_audio()
    
    def _create_narration_text(self, explanation: str) -> str:
        """Create text for narration."""
        # Clean explanation for speech
        clean_text = self._clean_explanation_text(explanation)
        
        # Add pauses and improve flow
        narration = f"Let's solve this CAT question step by step. {clean_text} This completes our solution."
        
        return narration
    
    def _create_silent_audio(self) -> Path:
        """Create silent audio as fallback."""
        from moviepy.editor import AudioClip
        
        audio_path = self.temp_dir / f"silent_{datetime.now().strftime('%H%M%S')}.mp3"
        
        # Create 10 seconds of silence
        silent_audio = AudioClip(lambda t: [0, 0], duration=10)
        silent_audio.write_audiofile(str(audio_path), verbose=False, logger=None)
        
        return audio_path
    
    def _combine_slides_and_audio(self, slides: List[Path], audio_path: Path, output_path: Path):
        """Combine slides and audio into video."""
        try:
            # Get audio duration
            audio = AudioFileClip(str(audio_path))
            total_duration = audio.duration
            slide_duration = total_duration / len(slides)
            
            # Create video clips from slides
            video_clips = []
            for slide_path in slides:
                # Convert PIL image to video clip
                clip = (VideoFileClip(str(slide_path), duration=slide_duration)
                       if slide_path.suffix.lower() in ['.mp4', '.avi'] 
                       else self._image_to_video_clip(slide_path, slide_duration))
                video_clips.append(clip)
            
            # Concatenate video clips
            from moviepy.editor import concatenate_videoclips
            final_video = concatenate_videoclips(video_clips)
            
            # Add audio
            final_video = final_video.set_audio(audio)
            
            # Write final video
            final_video.write_videofile(
                str(output_path),
                fps=1,  # Low FPS for slideshow
                verbose=False,
                logger=None
            )
            
            # Cleanup
            audio.close()
            final_video.close()
            for clip in video_clips:
                clip.close()
                
        except Exception as e:
            self.logger.error(f"Video combination failed: {e}")
            raise
    
    def _image_to_video_clip(self, image_path: Path, duration: float):
        """Convert static image to video clip."""
        from moviepy.editor import ImageClip
        return ImageClip(str(image_path)).set_duration(duration)
    
    def _cleanup_temp_files(self, temp_files: List[Path]):
        """Clean up temporary files."""
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {temp_file}: {e}")