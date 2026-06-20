"""
Credibility checker for resume trust signals.
Scores resume claims against evidence such as projects, GitHub profile data,
and internal consistency in the candidate's timeline.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import re

import requests


@dataclass
class CheckSignal:
    name: str
    score: float
    status: str
    summary: str
    evidence: List[str]


@dataclass
class CredibilityReport:
    overall_score: float
    fake_skills: CheckSignal
    github_validation: CheckSignal
    experience_consistency: CheckSignal
    flags: List[str]
    github_profile: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "fake_skills": asdict(self.fake_skills),
            "github_validation": asdict(self.github_validation),
            "experience_consistency": asdict(self.experience_consistency),
            "flags": self.flags,
            "github_profile": self.github_profile,
        }


class CredibilityChecker:
    """Estimate how credible a resume looks based on internal and external signals."""

    HIGH_SIGNAL_SKILLS = {
        "python", "java", "javascript", "typescript", "react", "node.js",
        "aws", "docker", "kubernetes", "machine learning", "deep learning",
        "nlp", "tensorflow", "pytorch", "sql", "postgresql", "mongodb", "git",
        "github", "data analysis", "transformers", "llm", "prompt engineering",
    }

    DATE_RANGE_PATTERN = re.compile(
        r"(?P<start>(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+)?(?P<start_year>19\d{2}|20\d{2})"
        r"\s*(?:-|to|–)\s*"
        r"(?P<end>(?:present|current|now)|(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+)?(?P<end_year>19\d{2}|20\d{2}))",
        re.IGNORECASE,
    )

    def __init__(self, timeout_seconds: float = 4.0):
        self.timeout_seconds = timeout_seconds

    def analyze(
        self,
        resume_data: Dict[str, Any],
        job_description: str = "",
        github_url: Optional[str] = None,
        github_profile: Optional[Dict[str, Any]] = None,
    ) -> CredibilityReport:
        github_url = github_url or resume_data.get("github") or self._extract_github_url(resume_data.get("raw_text", ""))
        if github_profile is None and github_url:
            github_profile = self._fetch_github_profile(github_url)

        fake_skills = self._check_fake_skills(resume_data, github_profile, job_description)
        github_validation = self._check_github_validation(github_url, github_profile)
        experience_consistency = self._check_experience_consistency(resume_data)

        overall_score = round(
            fake_skills.score * 0.4 +
            github_validation.score * 0.3 +
            experience_consistency.score * 0.3,
            2,
        )

        flags = []
        for signal in [fake_skills, github_validation, experience_consistency]:
            if signal.status == "high_risk":
                flags.append(signal.summary)

        return CredibilityReport(
            overall_score=overall_score,
            fake_skills=fake_skills,
            github_validation=github_validation,
            experience_consistency=experience_consistency,
            flags=flags,
            github_profile=github_profile or {},
        )

    def _check_fake_skills(
        self,
        resume_data: Dict[str, Any],
        github_profile: Optional[Dict[str, Any]],
        job_description: str,
    ) -> CheckSignal:
        claimed_skills = {skill.lower() for skill in resume_data.get("skills", [])}
        if not claimed_skills:
            return CheckSignal(
                name="Fake skills",
                score=45.0,
                status="review",
                summary="Very few explicit skills were extracted, so claims are hard to verify.",
                evidence=["No clear skills section or parsable skill evidence found."],
            )

        project_evidence = self._extract_project_evidence(resume_data.get("raw_text", ""))
        evidence_skills = {token.lower() for token in project_evidence}

        github_skills = set()
        if github_profile:
            github_skills = {
                skill.lower()
                for skill in github_profile.get("top_languages", []) + github_profile.get("topics", [])
            }

        supported = sorted(skill for skill in claimed_skills if skill in evidence_skills or skill in github_skills)
        unsupported = sorted(skill for skill in claimed_skills if skill in self.HIGH_SIGNAL_SKILLS and skill not in evidence_skills and skill not in github_skills)

        support_ratio = len(supported) / max(len(claimed_skills), 1)
        score = max(20.0, min(98.0, 55.0 + support_ratio * 45.0 - len(unsupported) * 4.0))

        if score >= 75:
            status = "verified"
            summary = "Most extracted skills are backed by project or GitHub evidence."
        elif score >= 50:
            status = "review"
            summary = "Some skills are supported, but several higher-signal claims need human review."
        else:
            status = "high_risk"
            summary = "Multiple claimed skills lack nearby project evidence or GitHub support."

        evidence = [
            f"Supported skills: {', '.join(supported[:8])}" if supported else "No strong project-backed skills were detected.",
        ]
        if unsupported:
            evidence.append(f"Unverified high-signal skills: {', '.join(unsupported[:8])}")
        if github_profile and github_profile.get("repo_count", 0):
            evidence.append(f"GitHub evidence reviewed across {github_profile['repo_count']} public repositories.")

        return CheckSignal("Fake skills", round(score, 2), status, summary, evidence)

    def _check_github_validation(
        self,
        github_url: Optional[str],
        github_profile: Optional[Dict[str, Any]],
    ) -> CheckSignal:
        if not github_url:
            return CheckSignal(
                name="GitHub validation",
                score=30.0,
                status="review",
                summary="No GitHub profile was provided or detected on the resume.",
                evidence=["Add a GitHub profile to validate project depth and recency."],
            )

        if not github_profile:
            return CheckSignal(
                name="GitHub validation",
                score=45.0,
                status="review",
                summary="A GitHub link exists, but live profile evidence could not be fetched.",
                evidence=["The app fell back to resume-only validation for this check."],
            )

        repo_count = github_profile.get("repo_count", 0)
        stars = github_profile.get("total_stars", 0)
        recent_activity = github_profile.get("recent_activity", 0)
        completeness_bonus = 10 if github_profile.get("bio") else 0

        score = min(98.0, 35.0 + repo_count * 4.0 + min(stars, 20) * 1.2 + min(recent_activity, 12) * 2.0 + completeness_bonus)

        if score >= 75:
            status = "verified"
            summary = "GitHub profile shows active public project evidence."
        elif score >= 50:
            status = "review"
            summary = "GitHub profile exists but public activity is moderate."
        else:
            status = "high_risk"
            summary = "GitHub presence is weak compared with technical claims."

        evidence = [
            f"Public repos: {repo_count}",
            f"Recent active repos: {recent_activity}",
            f"Top languages: {', '.join(github_profile.get('top_languages', [])[:5]) or 'None detected'}",
        ]
        return CheckSignal("GitHub validation", round(score, 2), status, summary, evidence)

    def _check_experience_consistency(self, resume_data: Dict[str, Any]) -> CheckSignal:
        raw_text = resume_data.get("raw_text", "")
        experience_entries = resume_data.get("experience", [])
        ranges = self._extract_date_ranges(raw_text)

        issues = []
        if len(experience_entries) <= 1:
            issues.append("Very limited structured experience entries were extracted.")
        if not ranges:
            issues.append("No clear employment date ranges were detected.")

        overlaps = self._find_overlaps(ranges)
        if overlaps:
            issues.append(f"Potential overlapping date ranges detected: {len(overlaps)}")

        years_claimed = self._extract_years_claimed(raw_text)
        timeline_span = self._estimate_timeline_span(ranges)
        if years_claimed and timeline_span and years_claimed - timeline_span >= 4:
            issues.append(f"Claimed experience ({years_claimed} years) looks high against the detected timeline ({timeline_span} years).")

        score = 88.0
        score -= len(issues) * 14.0
        score = max(25.0, min(98.0, score))

        if score >= 75:
            status = "verified"
            summary = "Experience timeline looks internally consistent."
        elif score >= 50:
            status = "review"
            summary = "Experience timeline is partially consistent but has gaps or low structure."
        else:
            status = "high_risk"
            summary = "Experience timeline has gaps or contradictions that should be reviewed."

        evidence = [
            f"Structured experience entries: {len(experience_entries)}",
            f"Detected date ranges: {len(ranges)}",
        ]
        evidence.extend(issues[:4])
        return CheckSignal("Experience consistency", round(score, 2), status, summary, evidence)

    def _extract_project_evidence(self, text: str) -> List[str]:
        lowered = text.lower()
        evidence = set()
        for skill in self.HIGH_SIGNAL_SKILLS:
            if skill in lowered:
                evidence.add(skill)
        return sorted(evidence)

    def _extract_github_url(self, text: str) -> Optional[str]:
        match = re.search(r"https?://(?:www\.)?github\.com/[A-Za-z0-9-]+", text, re.IGNORECASE)
        if match:
            return match.group(0)
        match = re.search(r"github\.com/[A-Za-z0-9-]+", text, re.IGNORECASE)
        return match.group(0) if match else None

    def _fetch_github_profile(self, github_url: str) -> Optional[Dict[str, Any]]:
        username = github_url.rstrip("/").split("/")[-1]
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "resume-analyzer"}

        try:
            user_resp = requests.get(
                f"https://api.github.com/users/{username}",
                headers=headers,
                timeout=self.timeout_seconds,
            )
            user_resp.raise_for_status()
            user = user_resp.json()

            repos_resp = requests.get(
                f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
                headers=headers,
                timeout=self.timeout_seconds,
            )
            repos_resp.raise_for_status()
            repos = repos_resp.json()
        except Exception:
            return None

        languages = {}
        topics = set()
        stars = 0
        recent_activity = 0
        for repo in repos:
            language = repo.get("language")
            if language:
                languages[language] = languages.get(language, 0) + 1
            stars += int(repo.get("stargazers_count", 0) or 0)
            if repo.get("pushed_at"):
                recent_activity += 1
            for topic in repo.get("topics", []):
                topics.add(topic)

        top_languages = [lang.lower() for lang, _count in sorted(languages.items(), key=lambda item: item[1], reverse=True)]
        return {
            "username": username,
            "name": user.get("name"),
            "bio": user.get("bio"),
            "followers": user.get("followers", 0),
            "public_repos": user.get("public_repos", 0),
            "repo_count": len(repos),
            "total_stars": stars,
            "recent_activity": recent_activity,
            "top_languages": top_languages[:8],
            "topics": sorted(topics)[:12],
        }

    def _extract_date_ranges(self, text: str) -> List[Tuple[int, int]]:
        ranges = []
        for match in self.DATE_RANGE_PATTERN.finditer(text):
            start_year = int(match.group("start_year"))
            end_value = match.group("end")
            end_year = int(match.group("end_year")) if match.group("end_year") else 2026 if end_value and end_value.lower() in {"present", "current", "now"} else start_year
            if end_year >= start_year:
                ranges.append((start_year, end_year))
        return ranges

    def _find_overlaps(self, ranges: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        overlaps = []
        ordered = sorted(ranges)
        for index in range(1, len(ordered)):
            prev = ordered[index - 1]
            current = ordered[index]
            if current[0] < prev[1]:
                overlaps.append((prev, current))
        return overlaps

    def _extract_years_claimed(self, text: str) -> Optional[int]:
        match = re.search(r"(\d+)\+?\s+years?\s+of\s+experience", text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _estimate_timeline_span(self, ranges: List[Tuple[int, int]]) -> Optional[int]:
        if not ranges:
            return None
        start = min(item[0] for item in ranges)
        end = max(item[1] for item in ranges)
        return max(0, end - start)


def analyze_resume_credibility(
    resume_data: Dict[str, Any],
    job_description: str = "",
    github_url: Optional[str] = None,
    github_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    checker = CredibilityChecker()
    return checker.analyze(resume_data, job_description, github_url, github_profile).to_dict()
