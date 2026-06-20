"""
Test script to verify all modules work correctly
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_parser():
    """Test resume parser module"""
    print("Testing Resume Parser...")
    from src.parser import ResumeParser

    parser = ResumeParser()
    print(f"  OK Parser initialized")
    print(f"  OK Skills tracked: {len(parser.COMMON_SKILLS)}")
    sample = parser._extract_structured_data(
        "Jane Doe\njane@example.com\nhttps://github.com/janedoe\nSkills\nPython AWS"
    )
    print(f"  OK GitHub extracted: {sample.github or 'missing'}")
    return True


def test_matcher():
    """Test semantic matcher module"""
    print("\nTesting Semantic Matcher...")
    from src.matcher import SemanticMatcher

    matcher = SemanticMatcher()
    print("  OK Matcher model loaded")

    resume_data = {
        "raw_text": "Python developer with machine learning experience",
        "skills": ["python", "machine learning"],
        "summary": "Experienced developer",
        "experience": [],
    }
    job_desc = "Looking for Python developer with ML skills"

    result = matcher.match_resume_to_job(resume_data, job_desc)
    print(f"  OK Match score: {result.overall_score:.2f}")
    return True


def test_skill_extractor():
    """Test skill extractor module"""
    print("\nTesting Skill Extractor...")
    from src.skill_extractor import SkillExtractor

    extractor = SkillExtractor()
    print("  OK Extractor initialized")
    print(f"  OK Categories: {len(extractor.SKILL_CATEGORIES)}")

    text = "Python developer with AWS and Docker experience"
    skills = extractor.extract_skills(text)
    print(f"  OK Extracted skills: {len(skills)} categories")
    return True


def test_classifier():
    """Test resume classifier module"""
    print("\nTesting Resume Classifier...")
    from src.classifier import ResumeClassifier

    classifier = ResumeClassifier()
    print("  OK Classifier initialized")
    print(f"  OK Categories: {len(classifier.categories)}")

    result = classifier.predict("Python machine learning data analysis")
    print(f"  OK Predicted: {result.category}")
    return True


def test_decision_engine():
    """Test decision engine module"""
    print("\nTesting Decision Engine...")
    from src.decision_engine import DecisionEngine

    engine = DecisionEngine()
    print("  OK Engine initialized")

    match_result = {
        "overall_score": 75,
        "skills_score": 80,
        "experience_score": 70,
        "summary_score": 65,
        "matched_skills": ["python", "sql"],
        "missing_skills": ["aws"],
    }
    resume_data = {
        "skills": ["python", "sql"],
        "experience": [{"text": "Software Engineer"}],
        "education": [{"degree": "BS"}],
        "email": "test@email.com",
        "summary": "Experienced developer",
    }

    decision = engine.decide(match_result, resume_data)
    print(f"  OK Decision: {decision.decision}")
    return True


def test_ats_checker():
    """Test ATS checker module"""
    print("\nTesting ATS Checker...")
    from src.ats_checker import ATSChecker

    checker = ATSChecker()
    print("  OK Checker initialized")

    resume_data = {
        "raw_text": "John Doe\nEmail: john@email.com\nSkills: Python\nExperience: 5 years",
        "name": "John Doe",
        "email": "john@email.com",
        "phone": "555-1234",
        "skills": ["Python"],
        "experience": [{"text": "Software Engineer"}],
        "education": [{"degree": "BS"}],
        "summary": "Experienced developer",
    }

    result = checker.check_resume(resume_data)
    print(f"  OK ATS Score: {result.score}")
    return True


def test_job_fetcher():
    """Test job fetcher module"""
    print("\nTesting Job Fetcher...")
    from src.job_fetcher import JobDataFetcher

    fetcher = JobDataFetcher()
    print("  OK Fetcher initialized")
    return True


def test_credibility_checker():
    """Test credibility checker module"""
    print("\nTesting Credibility Checker...")
    from src.credibility_checker import CredibilityChecker

    checker = CredibilityChecker()
    resume_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "github": "https://github.com/janedoe",
        "raw_text": (
            "Jane Doe\n"
            "5 years of experience\n"
            "Experience\n"
            "Software Engineer Jan 2020 - Dec 2022\n"
            "Senior Engineer Jan 2023 - Present\n"
            "Built NLP pipelines with Python, AWS, Docker, SQL and machine learning.\n"
        ),
        "skills": ["python", "aws", "docker", "sql", "machine learning"],
        "experience": [
            {"text": "Software Engineer Jan 2020 - Dec 2022", "has_date": True},
            {"text": "Senior Engineer Jan 2023 - Present", "has_date": True},
        ],
    }
    github_profile = {
        "username": "janedoe",
        "bio": "ML engineer",
        "repo_count": 4,
        "public_repos": 4,
        "total_stars": 7,
        "recent_activity": 4,
        "top_languages": ["python", "typescript"],
        "topics": ["nlp", "machine-learning", "docker"],
    }

    report = checker.analyze(
        resume_data,
        "Need Python, AWS and ML experience",
        github_profile=github_profile,
    )
    print(f"  OK Credibility score: {report.overall_score:.2f}")
    print(f"  OK Fake skills status: {report.fake_skills.status}")
    return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("AI Resume Analyzer - Module Tests")
    print("=" * 50)

    tests = [
        ("Parser", test_parser),
        ("Matcher", test_matcher),
        ("Skill Extractor", test_skill_extractor),
        ("Classifier", test_classifier),
        ("Decision Engine", test_decision_engine),
        ("ATS Checker", test_ats_checker),
        ("Job Fetcher", test_job_fetcher),
        ("Credibility Checker", test_credibility_checker),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\nOK {name} test PASSED")
        except Exception as e:
            failed += 1
            print(f"\nFAIL {name} test FAILED: {str(e)}")

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
