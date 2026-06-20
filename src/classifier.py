"""
Resume Classifier Module
Classifies resumes into job categories using TF-IDF and Logistic Regression
"""

import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score


@dataclass
class ClassificationResult:
    """Classification result"""
    category: str
    confidence: float
    probabilities: Dict[str, float]
    top_features: List[str]


class ResumeClassifier:
    """Classify resumes into job categories"""
    
    # Default job categories
    DEFAULT_CATEGORIES = [
        'Software Engineer',
        'Data Scientist',
        'Machine Learning Engineer',
        'Data Analyst',
        'DevOps Engineer',
        'Frontend Developer',
        'Backend Developer',
        'Full Stack Developer',
        'Product Manager',
        'QA Engineer',
        'UI/UX Designer',
        'Cloud Engineer',
        'Security Engineer',
        'Database Administrator',
        'Business Analyst'
    ]
    
    # Category keywords for initial training data generation
    CATEGORY_KEYWORDS = {
        'Software Engineer': ['programming', 'software', 'code', 'developer', 'engineering'],
        'Data Scientist': ['data science', 'statistics', 'analytics', 'insights', 'model'],
        'Machine Learning Engineer': ['machine learning', 'deep learning', 'ai', 'neural', 'ml'],
        'Data Analyst': ['data analysis', 'excel', 'tableau', 'visualization', 'reporting'],
        'DevOps Engineer': ['devops', 'ci/cd', 'jenkins', 'docker', 'kubernetes', 'automation'],
        'Frontend Developer': ['frontend', 'react', 'angular', 'vue', 'css', 'html', 'ui'],
        'Backend Developer': ['backend', 'api', 'database', 'server', 'node', 'django'],
        'Full Stack Developer': ['full stack', 'frontend', 'backend', 'mern', 'fullstack'],
        'Product Manager': ['product', 'roadmap', 'stakeholder', 'requirements', 'agile'],
        'QA Engineer': ['qa', 'testing', 'test', 'quality', 'automation', 'selenium'],
        'UI/UX Designer': ['design', 'ui', 'ux', 'figma', 'prototype', 'user experience'],
        'Cloud Engineer': ['cloud', 'aws', 'azure', 'gcp', 'infrastructure'],
        'Security Engineer': ['security', 'cybersecurity', 'vulnerability', 'penetration'],
        'Database Administrator': ['database', 'dba', 'sql', 'postgresql', 'mysql', 'oracle'],
        'Business Analyst': ['business', 'requirements', 'stakeholder', 'process', 'analysis']
    }
    
    def __init__(self, categories: Optional[List[str]] = None):
        """Initialize classifier"""
        self.categories = categories or self.DEFAULT_CATEGORIES
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english',
            min_df=2,
            max_df=0.95
        )
        self.model = LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight='balanced',
            random_state=42
        )
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        
        # Fit label encoder
        self.label_encoder.fit(self.categories)
    
    def train(self, texts: List[str], labels: List[str], save_path: Optional[str] = None):
        """Train the classifier"""
        # Vectorize texts
        X = self.vectorizer.fit_transform(texts)
        y = self.label_encoder.transform(labels)
        
        # Train model
        self.model.fit(X, y)
        self.is_trained = True
        
        # Save if path provided
        if save_path:
            self.save(save_path)
        
        print(f"Trained on {len(texts)} samples")
    
    def predict(self, text: str) -> ClassificationResult:
        """Predict category for a single text"""
        if not self.is_trained:
            # Use keyword-based prediction if not trained
            return self._keyword_predict(text)
        
        # Vectorize
        X = self.vectorizer.transform([text])
        
        # Predict
        pred_idx = self.model.predict(X)[0]
        pred_proba = self.model.predict_proba(X)[0]
        
        category = self.label_encoder.inverse_transform([pred_idx])[0]
        confidence = float(pred_proba[pred_idx])
        
        # Get probabilities for all categories
        probabilities = {
            cat: float(prob) 
            for cat, prob in zip(self.categories, pred_proba)
        }
        
        # Get top features
        top_features = self._get_top_features(X, pred_idx)
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            probabilities=probabilities,
            top_features=top_features
        )
    
    def _keyword_predict(self, text: str) -> ClassificationResult:
        """Fallback keyword-based prediction"""
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[category] = score
        
        # Normalize
        max_score = max(scores.values()) if scores.values() else 1
        for cat in scores:
            scores[cat] /= max_score
        
        # Get top category
        top_cat = max(scores, key=scores.get)
        confidence = scores[top_cat]
        
        return ClassificationResult(
            category=top_cat,
            confidence=confidence,
            probabilities=scores,
            top_features=[]
        )
    
    def _get_top_features(self, X, pred_idx: int) -> List[str]:
        """Get top contributing features for prediction"""
        feature_names = self.vectorizer.get_feature_names_out()
        coefs = self.model.coef_[0]
        
        # Get top positive and negative features
        top_positive_idx = np.argsort(coefs)[-5:][::-1]
        top_negative_idx = np.argsort(coefs)[:5]
        
        features = []
        for idx in list(top_positive_idx) + list(top_negative_idx):
            features.append(feature_names[idx])
        
        return features
    
    def batch_predict(self, texts: List[str]) -> List[ClassificationResult]:
        """Predict categories for multiple texts"""
        return [self.predict(text) for text in texts]
    
    def train_with_synthetic_data(self, sample_resumes: List[Dict]):
        """Train with synthetic data generated from sample resumes"""
        texts = []
        labels = []
        
        for resume in sample_resumes:
            # Generate text from resume
            text = self._resume_to_text(resume)
            category = resume.get('category', 'Software Engineer')
            
            texts.append(text)
            labels.append(category)
        
        self.train(texts, labels)
    
    def _resume_to_text(self, resume: Dict) -> str:
        """Convert resume dict to text for training"""
        parts = []
        
        if resume.get('skills'):
            parts.extend(resume['skills'])
        if resume.get('summary'):
            parts.append(resume['summary'])
        if resume.get('experience'):
            for exp in resume['experience']:
                if isinstance(exp, dict) and exp.get('text'):
                    parts.append(exp['text'])
        
        return ' '.join(parts)
    
    def save(self, path: str):
        """Save model to disk"""
        model_data = {
            'vectorizer': self.vectorizer,
            'model': self.model,
            'label_encoder': self.label_encoder,
            'categories': self.categories,
            'is_trained': self.is_trained
        }
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vectorizer = model_data['vectorizer']
        self.model = model_data['model']
        self.label_encoder = model_data['label_encoder']
        self.categories = model_data['categories']
        self.is_trained = model_data['is_trained']
        
        print(f"Model loaded from {path}")


def classify_resume(resume_data: Dict) -> Dict:
    """Convenience function to classify a resume"""
    classifier = ResumeClassifier()
    
    # Convert resume to text
    text = ""
    if resume_data.get('skills'):
        text += " ".join(resume_data['skills']) + " "
    if resume_data.get('summary'):
        text += resume_data['summary'] + " "
    if resume_data.get('raw_text'):
        text += resume_data['raw_text'][:1000]
    
    result = classifier.predict(text)
    
    return {
        'category': result.category,
        'confidence': result.confidence,
        'probabilities': result.probabilities,
        'top_features': result.top_features
    }


if __name__ == "__main__":
    print("Resume Classifier Module Loaded")
    classifier = ResumeClassifier()
    print(f"Categories: {len(classifier.categories)}")