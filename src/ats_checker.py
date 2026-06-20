"""
ATS (Applicant Tracking System) Checker Module
Analyzes resume compatibility with ATS systems
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ATSResult:
    """ATS compatibility result"""
    score: float
    issues: List[Dict[str, str]]
    suggestions: List[str]
    section_analysis: Dict[str, bool]
    keyword_density: Dict[str, float]


class ATSChecker:
    """Check resume ATS compatibility"""
    
    # Required sections for ATS
    REQUIRED_SECTIONS = [
        'contact', 'summary', 'experience', 'education', 'skills'
    ]
    
    # Section headers variations
    SECTION_HEADERS = {
        'contact': ['contact', 'info', 'details', 'profile'],
        'summary': ['summary', 'objective', 'profile', 'about'],
        'experience': ['experience', 'employment', 'work history', 'professional'],
        'education': ['education', 'academic', 'qualification'],
        'skills': ['skills', 'technical skills', 'competencies', 'expertise']
    }
    
    # Problematic patterns
    PROBLEMATIC_PATTERNS = {
        'tables': r'table',
        'headers_footers': r'(header|footer)',
        'columns': r'column|col',
        'text_boxes': r'text box|textbox',
        'images': r'(image|photo|picture)',
        'special_chars': r'[^\x00-\x7F]',
        'links': r'http|www\.',
        'custom_chars': r'[™®©]'
    }
    
    def __init__(self):
        self.min_keyword_count = 5
        self.max_keyword_density = 0.15
    
    def check_resume(
        self, 
        resume_data: Dict, 
        job_description: Optional[str] = None
    ) -> ATSResult:
        """
        Check ATS compatibility of a resume
        
        Args:
            resume_data: Parsed resume data
            job_description: Optional job description for keyword analysis
        
        Returns:
            ATSResult with score and details
        """
        issues = []
        suggestions = []
        section_analysis = {}
        
        raw_text = resume_data.get('raw_text', '')
        
        # Check sections
        section_analysis = self._check_sections(raw_text)
        
        # Check formatting issues
        formatting_issues = self._check_formatting(raw_text)
        issues.extend(formatting_issues)
        
        # Check contact info
        contact_issues = self._check_contact(resume_data)
        issues.extend(contact_issues)
        
        # Check keyword density
        keyword_density = self._analyze_keywords(raw_text, job_description)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            section_analysis, 
            formatting_issues, 
            keyword_density,
            resume_data
        )
        
        # Calculate score
        score = self._calculate_score(
            section_analysis, 
            formatting_issues, 
            keyword_density
        )
        
        return ATSResult(
            score=score,
            issues=issues,
            suggestions=suggestions,
            section_analysis=section_analysis,
            keyword_density=keyword_density
        )
    
    def _check_sections(self, text: str) -> Dict[str, bool]:
        """Check presence of required sections"""
        text_lower = text.lower()
        lines = text_lower.split('\n')
        
        section_analysis = {}
        
        for section, headers in self.SECTION_HEADERS.items():
            found = False
            for line in lines[:30]:  # Check first 30 lines
                if any(h in line for h in headers):
                    found = True
                    break
            section_analysis[section] = found
        
        return section_analysis
    
    def _check_formatting(self, text: str) -> List[Dict[str, str]]:
        """Check for formatting issues"""
        issues = []
        
        for issue_type, pattern in self.PROBLEMATIC_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                issues.append({
                    'type': issue_type,
                    'severity': 'high',
                    'message': f"Potential {issue_type.replace('_', ' ')} detected - may affect ATS parsing"
                })
        
        # Check for very short resume
        if len(text.split()) < 100:
            issues.append({
                'type': 'length',
                'severity': 'medium',
                'message': 'Resume appears too short - may not contain enough content'
            })
        
        # Check for very long resume
        if len(text.split()) > 1500:
            issues.append({
                'type': 'length',
                'severity': 'medium',
                'message': 'Resume may be too long - consider condensing'
            })
        
        # Check for bullet points
        if '-' not in text and '*' not in text:
            issues.append({
                'type': 'formatting',
                'severity': 'low',
                'message': 'No bullet points detected - consider using bullets for readability'
            })
        
        return issues
    
    def _check_contact(self, resume_data: Dict) -> List[Dict[str, str]]:
        """Check contact information"""
        issues = []
        
        if not resume_data.get('email'):
            issues.append({
                'type': 'contact',
                'severity': 'high',
                'message': 'Missing email address'
            })
        
        if not resume_data.get('phone'):
            issues.append({
                'type': 'contact',
                'severity': 'medium',
                'message': 'Missing phone number'
            })
        
        if not resume_data.get('name'):
            issues.append({
                'type': 'contact',
                'severity': 'high',
                'message': 'Missing name at the top of resume'
            })
        
        return issues
    
    def _analyze_keywords(
        self, 
        text: str, 
        job_description: Optional[str]
    ) -> Dict[str, float]:
        """Analyze keyword density"""
        words = text.lower().split()
        total_words = len(words)
        
        if total_words == 0:
            return {'density': 0, 'unique_ratio': 0}
        
        # Calculate unique word ratio
        unique_words = len(set(words))
        unique_ratio = unique_words / total_words
        
        # If job description provided, check for keyword matches
        if job_description:
            job_words = set(job_description.lower().split())
            resume_words = set(words)
            matches = job_words & resume_words
            match_ratio = len(matches) / len(job_words) if job_words else 0
        else:
            match_ratio = 0
        
        return {
            'density': unique_ratio,
            'unique_ratio': unique_ratio,
            'job_keyword_match': match_ratio,
            'total_words': total_words
        }
    
    def _generate_suggestions(
        self,
        section_analysis: Dict[str, bool],
        formatting_issues: List[Dict],
        keyword_density: Dict[str, float],
        resume_data: Dict
    ) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Section suggestions
        missing_sections = [s for s, found in section_analysis.items() if not found]
        if missing_sections:
            suggestions.append(f"Add missing sections: {', '.join(missing_sections)}")
        
        # Formatting suggestions
        high_severity = [i for i in formatting_issues if i.get('severity') == 'high']
        if high_severity:
            suggestions.append("Fix high-severity formatting issues for better ATS parsing")
        
        # Keyword suggestions
        if keyword_density.get('unique_ratio', 0) < 0.3:
            suggestions.append("Increase vocabulary variety - too many repeated words")
        
        if keyword_density.get('total_words', 0) < 200:
            suggestions.append("Add more content - resume appears too short")
        
        # Skills suggestions
        if len(resume_data.get('skills', [])) < 5:
            suggestions.append("Add more skills to improve visibility")
        
        # Experience suggestions
        if len(resume_data.get('experience', [])) < 2:
            suggestions.append("Add more work experience details")
        
        return suggestions
    
    def _calculate_score(
        self,
        section_analysis: Dict[str, bool],
        formatting_issues: List[Dict],
        keyword_density: Dict[str, float]
    ) -> float:
        """Calculate ATS score"""
        score = 100.0
        
        # Deduct for missing sections (15 points each)
        missing_count = sum(1 for found in section_analysis.values() if not found)
        score -= missing_count * 15
        
        # Deduct for formatting issues
        for issue in formatting_issues:
            severity = issue.get('severity', 'low')
            if severity == 'high':
                score -= 15
            elif severity == 'medium':
                score -= 10
            else:
                score -= 5
        
        # Bonus for good keyword density
        if keyword_density.get('unique_ratio', 0) > 0.4:
            score += 5
        
        return max(0, min(100, score))
    
    def check_keyword_optimization(
        self,
        resume_data: Dict,
        job_description: str
    ) -> Dict[str, any]:
        """Check keyword optimization for specific job"""
        resume_text = resume_data.get('raw_text', '').lower()
        job_text = job_description.lower()
        
        # Extract potential keywords from job
        job_keywords = self._extract_keywords(job_text)
        
        # Check which are in resume
        resume_words = set(resume_text.split())
        found = []
        missing = []
        
        for kw in job_keywords:
            if kw in resume_words:
                found.append(kw)
            else:
                missing.append(kw)
        
        return {
            'found_keywords': found,
            'missing_keywords': missing,
            'match_rate': len(found) / len(job_keywords) if job_keywords else 0,
            'suggestions': [f"Add '{kw}' to your resume" for kw in missing[:10]]
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text"""
        # Common technical terms
        keywords = []
        tech_terms = [
            'python', 'java', 'javascript', 'sql', 'aws', 'azure', 'docker',
            'kubernetes', 'machine learning', 'data analysis', 'agile', 'scrum',
            'project management', 'communication', 'leadership', 'problem-solving'
        ]
        
        text_lower = text.lower()
        for term in tech_terms:
            if term in text_lower:
                keywords.append(term)
        
        return keywords


def check_ats_compatibility(
    resume_data: Dict,
    job_description: Optional[str] = None
) -> Dict:
    """Convenience function to check ATS compatibility"""
    checker = ATSChecker()
    result = checker.check_resume(resume_data, job_description)
    
    return {
        'score': result.score,
        'issues': result.issues,
        'suggestions': result.suggestions,
        'section_analysis': result.section_analysis,
        'keyword_density': result.keyword_density
    }


if __name__ == "__main__":
    print("ATS Checker Module Loaded")
    checker = ATSChecker()
    print("Ready for ATS checks!")