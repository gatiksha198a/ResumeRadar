"""
Semantic Matcher Module
Compares resumes with job descriptions using sentence-transformers
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from sentence_transformers import SentenceTransformer, util


@dataclass
class MatchResult:
    """Semantic match result"""
    overall_score: float
    skills_score: float
    experience_score: float
    summary_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    similarity_details: Dict[str, float]


class SemanticMatcher:
    """Match resumes to job descriptions using semantic similarity"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the semantic matcher with a sentence-transformer model"""
        print(f"Loading sentence-transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("Model loaded successfully!")
        
        # Job-related keywords for better matching
        self.job_keywords = [
            'required', 'preferred', 'must have', 'experience', 'skills',
            'knowledge', 'ability', 'proficient', 'expert', 'familiar'
        ]
    
    def match_resume_to_job(
        self, 
        resume_data: Dict, 
        job_description: str,
        required_skills: Optional[List[str]] = None
    ) -> MatchResult:
        """
        Compare resume against job description
        
        Args:
            resume_data: Parsed resume dictionary
            job_description: Job description text
            required_skills: List of required skills (optional)
        
        Returns:
            MatchResult with scores and details
        """
        # Extract resume components
        resume_text = resume_data.get('raw_text', '')
        resume_skills = resume_data.get('skills', [])
        resume_summary = resume_data.get('summary', '')
        resume_experience = resume_data.get('experience', [])
        
        # Calculate individual scores
        skills_score = self._calculate_skills_score(resume_skills, required_skills or [], job_description)
        experience_score = self._calculate_experience_score(resume_text, job_description)
        summary_score = self._calculate_summary_score(resume_summary, job_description)
        
        # Calculate overall semantic similarity
        overall_score = self._calculate_overall_similarity(
            resume_text, job_description
        )
        
        # Find matched and missing skills
        matched_skills, missing_skills = self._analyze_skill_match(
            resume_skills, required_skills or []
        )
        
        return MatchResult(
            overall_score=overall_score,
            skills_score=skills_score,
            experience_score=experience_score,
            summary_score=summary_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            similarity_details={
                'semantic_similarity': overall_score,
                'skills_match': skills_score,
                'experience_match': experience_score,
                'summary_match': summary_score
            }
        )
    
    def _calculate_skills_score(
        self, 
        resume_skills: List[str], 
        required_skills: List[str],
        job_description: str
    ) -> float:
        """Calculate skills match score"""
        if not required_skills:
            # Extract skills from job description
            required_skills = self._extract_skills_from_job(job_description)
        
        if not required_skills:
            return 50.0  # Default if no required skills found
        
        resume_skills_lower = [s.lower() for s in resume_skills]
        required_skills_lower = [s.lower() for s in required_skills]
        
        matches = sum(1 for skill in required_skills_lower if any(skill in rs or rs in skill for rs in resume_skills_lower))
        
        score = (matches / len(required_skills_lower)) * 100
        return min(score, 100.0)
    
    def _extract_skills_from_job(self, job_description: str) -> List[str]:
        """Extract potential skills from job description"""
        common_tech_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
            'go', 'rust', 'scala', 'kotlin', 'swift', 'php', 'sql', 'html', 'css',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'git',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'data analysis', 'data science', 'nlp', 'computer vision',
            'agile', 'scrum', 'jira', 'rest api', 'graphql', 'mongodb',
            'postgresql', 'mysql', 'redis', 'elasticsearch', 'tableau'
        ]
        
        job_lower = job_description.lower()
        found_skills = []
        
        for skill in common_tech_skills:
            if skill in job_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _calculate_experience_score(self, resume_text: str, job_description: str) -> float:
        """Calculate experience match score using semantic similarity"""
        # Extract experience-related sections
        resume_exp = self._extract_experience_text(resume_text)
        job_exp = self._extract_experience_requirements(job_description)
        
        if not resume_exp or not job_exp:
            return 50.0
        
        # Calculate semantic similarity
        similarity = self._semantic_similarity(resume_exp, job_exp)
        
        return similarity * 100
    
    def _extract_experience_text(self, text: str) -> str:
        """Extract experience section from resume"""
        lines = text.split('\n')
        exp_text = []
        in_exp_section = False
        
        for line in lines:
            line_lower = line.lower()
            if 'experience' in line_lower or 'employment' in line_lower:
                in_exp_section = True
                continue
            if in_exp_section:
                if any(kw in line_lower for kw in ['education', 'skills', 'summary']):
                    break
                if line.strip():
                    exp_text.append(line.strip())
        
        return ' '.join(exp_text[:20])
    
    def _extract_experience_requirements(self, job_desc: str) -> str:
        """Extract experience requirements from job description"""
        lines = job_desc.split('\n')
        exp_text = []
        
        for line in lines:
            line_lower = line.lower()
            if 'experience' in line_lower or 'years' in line_lower:
                exp_text.append(line.strip())
        
        return ' '.join(exp_text[:10])
    
    def _calculate_summary_score(self, resume_summary: str, job_description: str) -> float:
        """Calculate how well resume summary matches job"""
        if not resume_summary:
            return 30.0
        
        return self._semantic_similarity(resume_summary, job_description) * 100
    
    def _calculate_overall_similarity(self, resume_text: str, job_description: str) -> float:
        """Calculate overall semantic similarity"""
        return self._semantic_similarity(resume_text, job_description)
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        # Truncate to avoid memory issues
        text1 = text1[:2000]
        text2 = text2[:2000]
        
        embeddings = self.model.encode([text1, text2], convert_to_tensor=True)
        similarity = util.cos_sim(embeddings[0], embeddings[1])
        
        return float(similarity[0][0])
    
    def _analyze_skill_match(
        self, 
        resume_skills: List[str], 
        required_skills: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Analyze which skills are matched and missing"""
        if not required_skills:
            return resume_skills, []
        
        resume_skills_lower = [s.lower() for s in resume_skills]
        matched = []
        missing = []
        
        for req_skill in required_skills:
            req_lower = req_skill.lower()
            if any(req_lower in rs or rs in req_lower for rs in resume_skills_lower):
                matched.append(req_skill)
            else:
                missing.append(req_skill)
        
        return matched, missing
    
    def batch_match(
        self, 
        resumes: List[Dict], 
        job_description: str,
        required_skills: Optional[List[str]] = None
    ) -> List[MatchResult]:
        """Match multiple resumes to a job description"""
        results = []
        
        for resume in resumes:
            result = self.match_resume_to_job(resume, job_description, required_skills)
            results.append(result)
        
        # Sort by overall score
        results.sort(key=lambda x: x.overall_score, reverse=True)
        
        return results
    
    def get_skill_embeddings(self, skills: List[str]) -> np.ndarray:
        """Get embeddings for a list of skills"""
        return self.model.encode(skills, convert_to_tensor=True)


def calculate_match_score(
    resume_data: Dict, 
    job_description: str,
    required_skills: Optional[List[str]] = None
) -> Dict:
    """Convenience function to calculate match score"""
    matcher = SemanticMatcher()
    result = matcher.match_resume_to_job(resume_data, job_description, required_skills)
    
    return {
        'overall_score': result.overall_score,
        'skills_score': result.skills_score,
        'experience_score': result.experience_score,
        'summary_score': result.summary_score,
        'matched_skills': result.matched_skills,
        'missing_skills': result.missing_skills,
        'details': result.similarity_details
    }


if __name__ == "__main__":
    # Test the matcher
    print("Semantic Matcher Module Loaded")
    print("Testing model initialization...")
    matcher = SemanticMatcher()
    print("Model ready for matching!")