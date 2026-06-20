"""
Hiring Decision Engine Module
Predicts hiring decisions based on resume-job matching scores
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle


@dataclass
class HiringDecision:
    """Hiring decision result"""
    decision: str  # Hire, Shortlist, Reject
    confidence: float
    score_breakdown: Dict[str, float]
    reasons: List[str]
    recommendations: List[str]


class DecisionEngine:
    """ML-based hiring decision engine"""
    
    def __init__(self):
        """Initialize decision engine"""
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Decision thresholds (can be tuned)
        self.thresholds = {
            'hire': 75.0,
            'shortlist': 50.0,
            'reject': 0.0
        }
    
    def prepare_features(
        self,
        match_result: Dict,
        resume_data: Dict,
        job_data: Optional[Dict] = None
    ) -> np.ndarray:
        """Prepare features for decision prediction"""
        features = []
        
        # Match scores
        features.append(match_result.get('overall_score', 0))
        features.append(match_result.get('skills_score', 0))
        features.append(match_result.get('experience_score', 0))
        features.append(match_result.get('summary_score', 0))
        
        # Resume quality indicators
        features.append(len(resume_data.get('skills', [])))
        features.append(len(resume_data.get('experience', [])))
        features.append(len(resume_data.get('education', [])))
        
        # Has contact info
        features.append(1.0 if resume_data.get('email') else 0.0)
        features.append(1.0 if resume_data.get('phone') else 0.0)
        
        # Has summary
        features.append(1.0 if resume_data.get('summary') else 0.0)
        
        # Missing skills ratio
        matched = len(match_result.get('matched_skills', []))
        missing = len(match_result.get('missing_skills', []))
        total = matched + missing
        features.append(missing / total if total > 0 else 0.5)
        
        return np.array(features).reshape(1, -1)
    
    def decide(
        self,
        match_result: Dict,
        resume_data: Dict,
        job_data: Optional[Dict] = None,
        use_ml: bool = True
    ) -> HiringDecision:
        """
        Make hiring decision based on match results
        
        Args:
            match_result: Result from semantic matcher
            resume_data: Parsed resume data
            job_data: Optional job data
            use_ml: Whether to use ML model or rule-based
        
        Returns:
            HiringDecision with decision, confidence, and recommendations
        """
        if use_ml and self.is_trained:
            return self._ml_decide(match_result, resume_data, job_data)
        else:
            return self._rule_based_decide(match_result, resume_data, job_data)
    
    def _ml_decide(
        self,
        match_result: Dict,
        resume_data: Dict,
        job_data: Optional[Dict]
    ) -> HiringDecision:
        """ML-based decision"""
        features = self.prepare_features(match_result, resume_data, job_data)
        features_scaled = self.scaler.transform(features)
        
        # Get prediction and probability
        pred = self.model.predict(features_scaled)[0]
        proba = self.model.predict_proba(features_scaled)[0]
        
        decisions = ['Reject', 'Shortlist', 'Hire']
        decision = decisions[pred]
        confidence = float(proba[pred])
        
        # Generate reasons and recommendations
        reasons = self._generate_reasons(match_result, resume_data)
        recommendations = self._generate_recommendations(match_result, resume_data)
        
        return HiringDecision(
            decision=decision,
            confidence=confidence,
            score_breakdown={
                'overall': match_result.get('overall_score', 0),
                'skills': match_result.get('skills_score', 0),
                'experience': match_result.get('experience_score', 0)
            },
            reasons=reasons,
            recommendations=recommendations
        )
    
    def _rule_based_decide(
        self,
        match_result: Dict,
        resume_data: Dict,
        job_data: Optional[Dict]
    ) -> HiringDecision:
        """Rule-based decision (default)"""
        overall = match_result.get('overall_score', 0)
        skills = match_result.get('skills_score', 0)
        
        # Calculate weighted score
        weighted_score = (
            overall * 0.4 +
            skills * 0.4 +
            (len(resume_data.get('experience', [])) * 5) +
            (len(resume_data.get('skills', [])) * 2)
        )
        
        # Determine decision
        if weighted_score >= self.thresholds['hire']:
            decision = 'Hire'
            confidence = min(weighted_score / 100, 0.95)
        elif weighted_score >= self.thresholds['shortlist']:
            decision = 'Shortlist'
            confidence = 0.6 + (weighted_score - 50) / 50 * 0.3
        else:
            decision = 'Reject'
            confidence = 0.5 + (100 - weighted_score) / 100 * 0.4
        
        # Generate reasons and recommendations
        reasons = self._generate_reasons(match_result, resume_data)
        recommendations = self._generate_recommendations(match_result, resume_data)
        
        return HiringDecision(
            decision=decision,
            confidence=confidence,
            score_breakdown={
                'overall': overall,
                'skills': skills,
                'experience': match_result.get('experience_score', 0),
                'weighted': weighted_score
            },
            reasons=reasons,
            recommendations=recommendations
        )
    
    def _generate_reasons(
        self,
        match_result: Dict,
        resume_data: Dict
    ) -> List[str]:
        """Generate decision reasons"""
        reasons = []
        
        overall = match_result.get('overall_score', 0)
        skills = match_result.get('skills_score', 0)
        
        if overall >= 70:
            reasons.append("Strong overall match with job requirements")
        elif overall >= 50:
            reasons.append("Moderate match with potential for growth")
        else:
            reasons.append("Below average match with the position")
        
        if skills >= 70:
            reasons.append("Excellent skill alignment")
        elif skills >= 50:
            reasons.append("Partial skill match - some gaps identified")
        else:
            reasons.append("Significant skill gaps")
        
        if resume_data.get('experience'):
            reasons.append(f"Has {len(resume_data['experience'])} experience entries")
        
        if resume_data.get('summary'):
            reasons.append("Professional summary present")
        
        missing = match_result.get('missing_skills', [])
        if missing:
            reasons.append(f"Missing key skills: {', '.join(missing[:3])}")
        
        return reasons
    
    def _generate_recommendations(
        self,
        match_result: Dict,
        resume_data: Dict
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        missing = match_result.get('missing_skills', [])
        if missing:
            recommendations.append(f"Learn: {', '.join(missing[:3])}")
        
        if not resume_data.get('summary'):
            recommendations.append("Add a professional summary")
        
        if len(resume_data.get('skills', [])) < 5:
            recommendations.append("Expand your skills section")
        
        if not resume_data.get('experience'):
            recommendations.append("Add work experience details")
        
        if match_result.get('overall_score', 0) < 60:
            recommendations.append("Tailor resume more closely to job description")
        
        if not resume_data.get('email'):
            recommendations.append("Add contact information")
        
        return recommendations[:5]  # Limit to 5
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """Train the decision model"""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        print(f"Decision model trained on {len(X)} samples")
    
    def save(self, path: str):
        """Save model"""
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'thresholds': self.thresholds,
            'is_trained': self.is_trained
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, path: str):
        """Load model"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.scaler = data['scaler']
        self.thresholds = data['thresholds']
        self.is_trained = data['is_trained']


def make_decision(
    match_result: Dict,
    resume_data: Dict,
    job_data: Optional[Dict] = None
) -> Dict:
    """Convenience function to make hiring decision"""
    engine = DecisionEngine()
    decision = engine.decide(match_result, resume_data, job_data)
    
    return {
        'decision': decision.decision,
        'confidence': decision.confidence,
        'score_breakdown': decision.score_breakdown,
        'reasons': decision.reasons,
        'recommendations': decision.recommendations
    }


if __name__ == "__main__":
    print("Decision Engine Module Loaded")
    engine = DecisionEngine()
    print("Ready for hiring decisions!")