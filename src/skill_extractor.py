"""
Skill Extraction Module
Extracts and categorizes skills from resume text using spaCy NER and pattern matching
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

@dataclass
class SkillCategory:
    """Category of skills"""
    name: str
    skills: List[str] = field(default_factory=list)
    level: str = "intermediate"  # beginner, intermediate, advanced


class SkillExtractor:
    """Extract and categorize skills from text using spaCy"""
    
    # Comprehensive skill taxonomy
    SKILL_CATEGORIES = {
        'programming_languages': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
            'go', 'rust', 'scala', 'kotlin', 'swift', 'php', 'perl', 'r',
            'matlab', 'julia', 'dart', 'elixir', 'haskell', 'clojure'
        ],
        'web_technologies': [
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'node',
            'express', 'django', 'flask', 'spring', 'asp.net', 'rest api',
            'graphql', 'webpack', 'sass', 'less', 'bootstrap', 'tailwind'
        ],
        'data_science_ml': [
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'keras', 'scikit-learn', 'sklearn', 'pandas', 'numpy', 'scipy',
            'nlp', 'natural language processing', 'computer vision', 'data analysis',
            'data visualization', 'statistics', 'regression', 'classification',
            'clustering', 'neural networks', 'transformers', 'bert', 'gpt'
        ],
        'cloud_devops': [
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
            'k8s', 'jenkins', 'terraform', 'ansible', 'ci/cd', 'devops',
            'git', 'github', 'gitlab', 'bitbucket', 'jira', 'cloudformation'
        ],
        'databases': [
            'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis',
            'elasticsearch', 'oracle', 'sqlite', 'nosql', 'dynamodb',
            'firebase', 'cassandra', 'mariadb', 'plsql', 'tsql'
        ],
        'soft_skills': [
            'leadership', 'communication', 'teamwork', 'problem-solving',
            'analytical', 'project management', 'agile', 'scrum', 'kanban',
            'time management', 'critical thinking', 'adaptability'
        ],
        'tools_software': [
            'linux', 'unix', 'windows', 'macos', 'networking', 'security',
            'testing', 'selenium', 'appium', 'junit', 'pytest', 'jira',
            'confluence', 'tableau', 'power bi', 'excel', 'office'
        ],
        'mobile_development': [
            'ios', 'android', 'react native', 'flutter', 'xamarin',
            'mobile development', 'app development', 'swiftui', 'jetpack'
        ],
        'data_engineering': [
            'etl', 'data pipeline', 'spark', 'hadoop', 'hive', 'airflow',
            'dbt', 'snowflake', 'bigquery', 'data warehouse', 'streaming'
        ]
    }
    
    # Skill level indicators
    LEVEL_INDICATORS = {
        'advanced': ['expert', 'advanced', 'senior', 'lead', 'architect', 'master'],
        'intermediate': ['proficient', 'intermediate', 'experienced', 'solid'],
        'beginner': ['familiar', 'basic', 'beginner', 'learning', 'introductory']
    }
    
    def __init__(self, model: str = "en_core_web_sm"):
        """Initialize skill extractor.

        Skill detection is pattern-based, so the Streamlit app can run without a
        hosted spaCy model download.
        """
        self.nlp = None
        
        # Build skill lookup
        self._build_skill_lookup()
    
    def _build_skill_lookup(self):
        """Build lowercase skill lookup for fast matching"""
        self.skill_lookup: Set[str] = set()
        self.category_map: Dict[str, str] = {}
        
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                self.skill_lookup.add(skill.lower())
                self.category_map[skill.lower()] = category
    
    def extract_skills(self, text: str) -> Dict[str, SkillCategory]:
        """Extract all skills from text and categorize them"""
        text_lower = text.lower()
        found_skills: Dict[str, Set[str]] = {cat: set() for cat in self.SKILL_CATEGORIES.keys()}
        
        # Direct skill matching
        for skill in self.skill_lookup:
            if skill in text_lower:
                category = self.category_map.get(skill)
                if category:
                    found_skills[category].add(skill)
        
        # Phrase matching for multi-word skills
        multi_word_skills = [
            'machine learning', 'deep learning', 'natural language processing',
            'computer vision', 'data analysis', 'data visualization',
            'project management', 'rest api', 'ci/cd', 'google cloud'
        ]
        
        for phrase in multi_word_skills:
            if phrase in text_lower:
                category = self.category_map.get(phrase)
                if category:
                    found_skills[category].add(phrase)
        
        # Build result
        result = {}
        for category, skills in found_skills.items():
            if skills:
                level = self._determine_skill_level(text_lower, list(skills))
                result[category] = SkillCategory(
                    name=category,
                    skills=sorted(list(skills)),
                    level=level
                )
        
        return result
    
    def _determine_skill_level(self, text: str, skills: List[str]) -> str:
        """Determine skill level based on context"""
        text_lower = text.lower()
        
        for skill in skills:
            # Look for skill and surrounding context
            idx = text_lower.find(skill)
            if idx >= 0:
                context = text_lower[max(0, idx-50):min(len(text), idx+50)]
                
                for level, indicators in self.LEVEL_INDICATORS.items():
                    if any(ind in context for ind in indicators):
                        return level
        
        return "intermediate"  # Default
    
    def extract_tech_stack(self, text: str) -> List[str]:
        """Extract technical skills as a flat list"""
        categories = self.extract_skills(text)
        
        all_skills = []
        for cat in categories.values():
            all_skills.extend(cat.skills)
        
        return sorted(all_skills)
    
    def compare_skills(
        self, 
        resume_skills: List[str], 
        job_skills: List[str]
    ) -> Dict[str, any]:
        """Compare resume skills to job requirements"""
        resume_set = set(s.lower() for s in resume_skills)
        job_set = set(s.lower() for s in job_skills)
        
        matched = resume_set & job_set
        missing = job_set - resume_set
        extra = resume_set - job_set
        
        match_rate = len(matched) / len(job_set) * 100 if job_set else 0
        
        return {
            'matched': list(matched),
            'missing': list(missing),
            'extra': list(extra),
            'match_rate': round(match_rate, 2),
            'matched_count': len(matched),
            'required_count': len(job_set)
        }
    
    def get_skill_gaps(self, resume_skills: List[str], job_skills: List[str]) -> List[Dict]:
        """Get learning recommendations for missing skills"""
        comparison = self.compare_skills(resume_skills, job_skills)
        
        gaps = []
        for skill in comparison['missing']:
            gaps.append({
                'skill': skill,
                'category': self.category_map.get(skill, 'unknown'),
                'priority': 'high' if skill in self._get_critical_skills() else 'medium',
                'learning_resources': self._get_learning_resources(skill)
            })
        
        return sorted(gaps, key=lambda x: 0 if x['priority'] == 'high' else 1)
    
    def _get_critical_skills(self) -> List[str]:
        """Get list of critical/hot skills"""
        return ['python', 'machine learning', 'aws', 'docker', 'kubernetes', 'sql']
    
    def _get_learning_resources(self, skill: str) -> List[Dict]:
        """Get learning resource suggestions for a skill"""
        resources = {
            'python': [
                {'platform': 'Coursera', 'course': 'Python for Everybody'},
                {'platform': 'freeCodeCamp', 'course': 'Learn Python'}
            ],
            'machine learning': [
                {'platform': 'Coursera', 'course': 'Machine Learning by Andrew Ng'},
                {'platform': 'fast.ai', 'course': 'Practical Deep Learning'}
            ],
            'aws': [
                {'platform': 'AWS Free Tier', 'course': 'AWS Cloud Practitioner'},
                {'platform': 'A Cloud Guru', 'course': 'AWS Solutions Architect'}
            ],
            'sql': [
                {'platform': 'Kaggle', 'course': 'SQL Tutorial'},
                {'platform': 'LeetCode', 'course': 'SQL Problems'}
            ]
        }
        
        return resources.get(skill, [{'platform': 'YouTube', 'course': f'{skill} tutorial'}])


def extract_all_skills(text: str) -> Dict:
    """Convenience function to extract skills"""
    extractor = SkillExtractor()
    categories = extractor.extract_skills(text)
    
    return {
        'categories': {k: {'skills': v.skills, 'level': v.level} for k, v in categories.items()},
        'all_skills': extractor.extract_tech_stack(text)
    }


if __name__ == "__main__":
    print("Skill Extractor Module Loaded")
    extractor = SkillExtractor()
    print(f"Skill categories: {len(extractor.SKILL_CATEGORIES)}")
    print(f"Total skills tracked: {len(extractor.skill_lookup)}")
