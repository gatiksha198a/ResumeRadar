"""
FastAPI Backend for Resume Analyzer
Provides REST API endpoints for resume analysis
"""

import os
import io
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import our modules
from src.parser import ResumeParser, parse_resume
from src.matcher import SemanticMatcher, calculate_match_score
from src.skill_extractor import SkillExtractor, extract_all_skills
from src.classifier import ResumeClassifier, classify_resume
from src.decision_engine import DecisionEngine, make_decision
from src.ats_checker import ATSChecker, check_ats_compatibility
from src.job_fetcher import JobDataFetcher, fetch_jobs
from src.credibility_checker import analyze_resume_credibility


# Initialize FastAPI app
app = FastAPI(
    title="AI Resume Analyzer API",
    description="Production-level AI Resume Analyzer & Hiring Intelligence Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class JobDescriptionRequest(BaseModel):
    job_description: str
    required_skills: Optional[List[str]] = None


class MatchRequest(BaseModel):
    resume_data: Dict[str, Any]
    job_description: str
    required_skills: Optional[List[str]] = None
    github_url: Optional[str] = None


class BatchMatchRequest(BaseModel):
    resumes: List[Dict[str, Any]]
    job_description: str
    required_skills: Optional[List[str]] = None


class JobSearchRequest(BaseModel):
    keyword: str
    location: str = "us"
    limit: int = 20


# Initialize components (lazy loading)
parser = None
matcher = None
skill_extractor = None
classifier = None
decision_engine = None
ats_checker = None
job_fetcher = None


def get_parser():
    global parser
    if parser is None:
        parser = ResumeParser()
    return parser


def get_matcher():
    global matcher
    if matcher is None:
        matcher = SemanticMatcher()
    return matcher


def get_skill_extractor():
    global skill_extractor
    if skill_extractor is None:
        skill_extractor = SkillExtractor()
    return skill_extractor


def get_classifier():
    global classifier
    if classifier is None:
        classifier = ResumeClassifier()
    return classifier


def get_decision_engine():
    global decision_engine
    if decision_engine is None:
        decision_engine = DecisionEngine()
    return decision_engine


def get_ats_checker():
    global ats_checker
    if ats_checker is None:
        ats_checker = ATSChecker()
    return ats_checker


def get_job_fetcher():
    global job_fetcher
    if job_fetcher is None:
        job_fetcher = JobDataFetcher()
    return job_fetcher


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Resume Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "parse_resume": "/api/parse-resume",
            "analyze_resume": "/api/analyze-resume",
            "match_resume": "/api/match-resume",
            "batch_match": "/api/batch-match",
            "ats_check": "/api/ats-check",
            "search_jobs": "/api/search-jobs",
            "full_analysis": "/api/full-analysis"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Resume Analyzer"}


@app.post("/api/parse-resume")
async def parse_resume_endpoint(
    file: UploadFile = File(...),
):
    """Parse a resume file (PDF or DOCX)"""
    try:
        # Read file
        content = await file.read()
        
        # Parse resume
        parser = get_parser()
        parsed = parser.parse_file(content, file.filename)
        result = parser.to_dict(parsed)
        
        return {
            "success": True,
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-resume")
async def analyze_resume_endpoint(request: Dict[str, Any]):
    """Analyze a parsed resume"""
    try:
        resume_data = request.get('resume_data')
        
        if not resume_data:
            raise HTTPException(status_code=400, detail="resume_data is required")
        
        # Extract skills
        skill_extractor = get_skill_extractor()
        skills_result = skill_extractor.extract_skills(resume_data.get('raw_text', ''))
        
        # Classify resume
        classifier = get_classifier()
        classification = classify_resume(resume_data)
        
        # Check ATS
        ats_checker = get_ats_checker()
        ats_result = check_ats_compatibility(resume_data)
        
        return {
            "success": True,
            "data": {
                "skills": skills_result,
                "classification": classification,
                "ats_check": ats_result,
                "credibility": analyze_resume_credibility(resume_data)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match-resume")
async def match_resume_endpoint(request: MatchRequest):
    """Match a resume against a job description"""
    try:
        # Calculate match score
        matcher = get_matcher()
        match_result = matcher.match_resume_to_job(
            request.resume_data,
            request.job_description,
            request.required_skills
        )
        
        # Make hiring decision
        decision_engine = get_decision_engine()
        decision = decision_engine.decide(
            {
                'overall_score': match_result.overall_score,
                'skills_score': match_result.skills_score,
                'experience_score': match_result.experience_score,
                'summary_score': match_result.summary_score,
                'matched_skills': match_result.matched_skills,
                'missing_skills': match_result.missing_skills
            },
            request.resume_data
        )
        credibility = analyze_resume_credibility(
            request.resume_data,
            request.job_description,
            request.github_url,
        )
        
        return {
            "success": True,
            "data": {
                "match_result": {
                    "overall_score": match_result.overall_score,
                    "skills_score": match_result.skills_score,
                    "experience_score": match_result.experience_score,
                    "summary_score": match_result.summary_score,
                    "matched_skills": match_result.matched_skills,
                    "missing_skills": match_result.missing_skills
                },
                "decision": {
                    "decision": decision.decision,
                    "confidence": decision.confidence,
                    "reasons": decision.reasons,
                    "recommendations": decision.recommendations
                },
                "credibility": credibility
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-match")
async def batch_match_endpoint(request: BatchMatchRequest):
    """Match multiple resumes against a job description"""
    try:
        matcher = get_matcher()
        decision_engine = get_decision_engine()
        
        results = []
        
        for resume in request.resumes:
            # Calculate match
            match_result = matcher.match_resume_to_job(
                resume,
                request.job_description,
                request.required_skills
            )
            
            # Make decision
            decision = decision_engine.decide(
                {
                    'overall_score': match_result.overall_score,
                    'skills_score': match_result.skills_score,
                    'experience_score': match_result.experience_score,
                    'summary_score': match_result.summary_score,
                    'matched_skills': match_result.matched_skills,
                    'missing_skills': match_result.missing_skills
                },
                resume
            )
            
            results.append({
                "resume_name": resume.get('name', 'Unknown'),
                "overall_score": match_result.overall_score,
                "decision": decision.decision,
                "confidence": decision.confidence,
                "credibility_score": analyze_resume_credibility(resume, request.job_description).get("overall_score"),
                "matched_skills": match_result.matched_skills,
                "missing_skills": match_result.missing_skills
            })
        
        # Sort by score
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Add rankings
        for i, r in enumerate(results):
            r['rank'] = i + 1
        
        return {
            "success": True,
            "data": {
                "total_resumes": len(results),
                "results": results
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ats-check")
async def ats_check_endpoint(request: Dict[str, Any]):
    """Check ATS compatibility of a resume"""
    try:
        resume_data = request.get('resume_data')
        job_description = request.get('job_description')
        
        if not resume_data:
            raise HTTPException(status_code=400, detail="resume_data is required")
        
        ats_checker = get_ats_checker()
        result = ats_checker.check_resume(resume_data, job_description)
        
        # If job description provided, also check keyword optimization
        if job_description:
            keyword_result = ats_checker.check_keyword_optimization(
                resume_data, job_description
            )
        else:
            keyword_result = None
        
        return {
            "success": True,
            "data": {
                "ats_score": result.score,
                "issues": result.issues,
                "suggestions": result.suggestions,
                "section_analysis": result.section_analysis,
                "keyword_analysis": keyword_result
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search-jobs")
async def search_jobs_endpoint(request: JobSearchRequest):
    """Search for jobs using free APIs"""
    try:
        job_fetcher = get_job_fetcher()
        jobs = job_fetcher.fetch_jobs_by_keyword(
            request.keyword,
            request.location,
            sources=['remotive']
        )
        
        return {
            "success": True,
            "data": {
                "total": len(jobs),
                "jobs": [
                    {
                        "job_id": job.job_id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "description": job.description[:500],
                        "skills": job.skills,
                        "job_type": job.job_type,
                        "source": job.source,
                        "url": job.url
                    }
                    for job in jobs[:request.limit]
                ]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/full-analysis")
async def full_analysis_endpoint(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    required_skills: Optional[str] = Form(None)
):
    """Full analysis: parse resume, match to job, make decision"""
    try:
        # Parse resume
        content = await file.read()
        parser = get_parser()
        parsed = parser.parse_file(content, file.filename)
        resume_data = parser.to_dict(parsed)
        
        # Parse required skills
        skills_list = None
        if required_skills:
            skills_list = [s.strip() for s in required_skills.split(',')]
        
        # Match to job
        matcher = get_matcher()
        match_result = matcher.match_resume_to_job(
            resume_data,
            job_description,
            skills_list
        )
        
        # Make decision
        decision_engine = get_decision_engine()
        decision = decision_engine.decide(
            {
                'overall_score': match_result.overall_score,
                'skills_score': match_result.skills_score,
                'experience_score': match_result.experience_score,
                'summary_score': match_result.summary_score,
                'matched_skills': match_result.matched_skills,
                'missing_skills': match_result.missing_skills
            },
            resume_data
        )
        
        # ATS check
        ats_checker = get_ats_checker()
        ats_result = ats_checker.check_resume(resume_data, job_description)
        
        # Extract skills
        skill_extractor = get_skill_extractor()
        skills_result = skill_extractor.extract_skills(resume_data.get('raw_text', ''))
        
        # Classify
        classification = classify_resume(resume_data)
        credibility = analyze_resume_credibility(resume_data, job_description)
        
        return {
            "success": True,
            "data": {
                "resume": {
                    "name": resume_data.get('name'),
                    "email": resume_data.get('email'),
                    "skills_count": len(resume_data.get('skills', [])),
                    "experience_count": len(resume_data.get('experience', []))
                },
                "match": {
                    "overall_score": round(match_result.overall_score, 2),
                    "skills_score": round(match_result.skills_score, 2),
                    "experience_score": round(match_result.experience_score, 2),
                    "matched_skills": match_result.matched_skills,
                    "missing_skills": match_result.missing_skills
                },
                "decision": {
                    "decision": decision.decision,
                    "confidence": round(decision.confidence, 2),
                    "reasons": decision.reasons,
                    "recommendations": decision.recommendations
                },
                "ats": {
                    "score": ats_result.score,
                    "issues": ats_result.issues,
                    "suggestions": ats_result.suggestions
                },
                "credibility": credibility,
                "classification": classification,
                "skills": skills_result
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
