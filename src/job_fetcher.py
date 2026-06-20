"""
Job Data Fetcher Module
Fetches job data from multiple sources: Remotive, Adzuna, Unstop, Internshala, Glassdoor
"""

import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
import re
from bs4 import BeautifulSoup


@dataclass
class JobData:
    """Job data structure"""
    job_id: str
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    skills: List[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    job_type: str
    posted_date: str
    source: str
    url: str


class JobDataFetcher:
    """Fetch job data from free APIs"""
    
    # Remotive API (completely free)
    REMOTIVE_API = "https://remotive.com/api/remote-jobs"
    
    # Adzuna API (free tier)
    ADZUNA_API = "https://api.adzuna.com/v1/api/jobs"
    
    # Unstop API (Indian jobs/internships)
    UNSTOP_API = "https://www.unstop.com"
    
    # Internshala API (internships)
    INTERNSHALA_API = "https://www.internshala.com"
    
    # Glassdoor (using search)
    GLASSDOOR_API = "https://www.glassdoor.com"
    LOCATION_SYNONYMS = {
        "global": ["worldwide", "global", "anywhere", "remote"],
        "us": ["united states", "usa", "us", "u.s.", "america"],
        "uk": ["united kingdom", "uk", "u.k.", "britain", "england", "london"],
        "ca": ["canada", "ca", "toronto", "vancouver", "montreal"],
        "au": ["australia", "au", "sydney", "melbourne", "brisbane"],
        "de": ["germany", "de", "berlin", "munich", "hamburg"],
        "fr": ["france", "fr", "paris", "lyon", "marseille"],
        "in": ["india", "in", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "delhi", "chennai"],
        "europe": ["europe", "eu", "european union", "emea"],
        "asia": ["asia", "apac", "asian"],
        "delhi ncr": ["delhi ncr", "new delhi", "gurugram", "gurgaon", "noida", "faridabad", "ghaziabad"],
        "bengaluru urban": ["bengaluru urban", "bengaluru", "bangalore"],
        "mumbai": ["mumbai", "navi mumbai", "thane"],
        "pune": ["pune", "pimpri", "chinchwad"],
        "hyderabad": ["hyderabad"],
        "chennai": ["chennai"],
        "kolkata": ["kolkata", "calcutta", "howrah"],
        "ahmedabad": ["ahmedabad", "gandhinagar"],
        "kochi": ["kochi", "cochin"],
        "san francisco": ["san francisco", "bay area", "oakland", "san jose"],
        "los angeles": ["los angeles", "anaheim", "long beach"],
        "new york city": ["new york city", "new york", "brooklyn", "queens", "manhattan"],
        "seattle": ["seattle", "bellevue", "redmond"],
        "chicago": ["chicago", "naperville", "schaumburg"],
        "boston": ["boston", "cambridge", "somerville"],
        "london": ["london"],
        "manchester": ["manchester"],
        "toronto": ["toronto", "mississauga", "brampton"],
        "vancouver": ["vancouver", "surrey", "burnaby"],
        "montreal": ["montreal", "laval"],
        "calgary": ["calgary"],
        "sydney": ["sydney"],
        "melbourne": ["melbourne"],
        "brisbane": ["brisbane", "gold coast", "sunshine coast"],
        "perth": ["perth", "fremantle"],
    }
    MULTILINGUAL_KEYWORDS = {
        "developer": ["developer", "desarrollador", "developpeur", "entwickler", "sviluppatore", "desenvolvedor", "विकासक", "डेवलपर"],
        "engineer": ["engineer", "ingeniero", "ingenieur", "ingenieurin", "engenheiro", "ingegnere", "अभियंता", "इंजीनियर"],
        "data scientist": ["data scientist", "cientifico de datos", "data scientist", "datenwissenschaftler", "cientista de dados", "डेटा साइंटिस्ट"],
        "data analyst": ["data analyst", "analista de datos", "analyste de donnees", "datenanalyst", "analista de dados", "डेटा विश्लेषक"],
        "python": ["python", "piton", "पाइथन"],
        "java": ["java"],
        "javascript": ["javascript", "js", "जावास्क्रिप्ट"],
        "machine learning": ["machine learning", "aprendizaje automatico", "apprentissage automatique", "maschinelles lernen", "aprendizado de maquina", "मशीन लर्निंग"],
        "designer": ["designer", "disenador", "designer", "gestalter", "डिज़ाइनर"],
        "marketing": ["marketing", "mercadotecnia", "marketing", "विपणन"],
        "sales": ["sales", "ventas", "ventes", "vertrieb", "vendas", "बिक्री"],
        "remote": ["remote", "remoto", "a distance", "fernarbeit", "remoto", "दूरस्थ"],
    }
    
    def __init__(self, adzuna_app_id: Optional[str] = None, adzuna_app_key: Optional[str] = None):
        self.adzuna_app_id = adzuna_app_id
        self.adzuna_app_key = adzuna_app_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ResumeAnalyzer/1.0'
        })
    
    def fetch_remote_jobs(
        self, 
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[JobData]:
        """Fetch remote jobs from Remotive API"""
        jobs = []
        
        try:
            params = {'limit': limit}
            if category:
                params['category'] = category
            if search:
                params['search'] = search
            
            response = self.session.get(self.REMOTIVE_API, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            job_list = data.get('jobs', [])
            
            for job in job_list:
                # Extract skills from description
                skills = self._extract_skills(job.get('description', ''))
                
                jobs.append(JobData(
                    job_id=f"remotive_{job.get('id')}",
                    title=job.get('title', ''),
                    company=job.get('company_name', ''),
                    location=job.get('candidate_required_location', 'Remote'),
                    description=job.get('description', ''),
                    requirements=self._extract_requirements(job.get('description', '')),
                    skills=skills,
                    salary_min=None,
                    salary_max=None,
                    job_type=job.get('job_type', ''),
                    posted_date=job.get('publication_date', ''),
                    source='remotive',
                    url=job.get('url', '')
                ))
            
        except Exception as e:
            print(f"Error fetching from Remotive: {e}")
        
        return jobs
    
    def fetch_adzuna_jobs(
        self,
        keyword: str,
        location: str = "us",
        limit: int = 50
    ) -> List[JobData]:
        """Fetch jobs from Adzuna API (requires API keys)"""
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("Adzuna API keys not configured - skipping")
            return []
        
        jobs = []
        
        try:
            url = f"{self.ADZUNA_API}/{location}/search"
            params = {
                'app_id': self.adzuna_app_id,
                'app_key': self.adzuna_app_key,
                'what': keyword,
                'results_per_page': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            for job in results:
                skills = self._extract_skills(job.get('description', ''))
                
                # Parse salary
                salary_min = None
                salary_max = None
                if job.get('salary_min'):
                    salary_min = float(job['salary_min'])
                if job.get('salary_max'):
                    salary_max = float(job['salate_max'])
                
                jobs.append(JobData(
                    job_id=f"adzuna_{job.get('id')}",
                    title=job.get('title', ''),
                    company=job.get('company', {}).get('display_name', ''),
                    location=job.get('location', {}).get('display_name', ''),
                    description=job.get('description', ''),
                    requirements=self._extract_requirements(job.get('description', '')),
                    skills=skills,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    job_type=job.get('contract_type', ''),
                    posted_date=job.get('created', ''),
                    source='adzuna',
                    url=job.get('url', '')
                ))
            
        except Exception as e:
            print(f"Error fetching from Adzuna: {e}")
        
        return jobs
    
    def fetch_unstop_jobs(
        self,
        keyword: str,
        limit: int = 30
    ) -> List[JobData]:
        """Fetch jobs from Unstop (Indian jobs and internships)"""
        jobs = []
        
        try:
            # Unstop search URL
            search_url = f"{self.UNSTOP_API}/api/stats/searchListingData"
            
            params = {
                'opportunity': 'internships',
                'search': keyword,
                'pageNo': 1
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                listings = data.get('data', {}).get('data', [])
                
                for job in listings[:limit]:
                    job_id = job.get('id', str(time.time()))
                    title = job.get('name', 'Internship Opportunity')
                    company = job.get('company_name', job.get('organization', 'Unknown'))
                    location = job.get('location', 'India')
                    
                    # Extract skills from title and description
                    description = job.get('description', '') or job.get('detail', '')
                    skills = self._extract_skills(f"{title} {description}")
                    
                    jobs.append(JobData(
                        job_id=f"unstop_{job_id}",
                        title=title,
                        company=company,
                        location=location,
                        description=description[:1000],
                        requirements=self._extract_requirements(description),
                        skills=skills,
                        salary_min=None,
                        salary_max=None,
                        job_type='Internship',
                        posted_date=job.get('posted_date', ''),
                        source='unstop',
                        url=f"{self.UNSTOP_API}/internships/{job_id}"
                    ))
        
        except Exception as e:
            print(f"Error fetching from Unstop: {e}")
        
        return jobs
    
    def fetch_internshala_jobs(
        self,
        keyword: str,
        limit: int = 30
    ) -> List[JobData]:
        """Fetch internships from Internshala"""
        jobs = []
        
        try:
            search_url = f"{self.INTERNSHALA_API}/internships/"
            
            # Use web scraping with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            params = {
                'search': keyword
            }
            
            response = self.session.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all internship cards
                internship_cards = soup.find_all('div', class_=['internship_card', 'card'])
                
                for card in internship_cards[:limit]:
                    try:
                        # Extract job details from HTML
                        title_elem = card.find('h3') or card.find('h4')
                        title = title_elem.get_text(strip=True) if title_elem else 'Internship'
                        
                        company_elem = card.find('p', class_=['company_name', 'organization'])
                        company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
                        
                        location_elem = card.find('p', class_=['location', 'job_location'])
                        location = location_elem.get_text(strip=True) if location_elem else 'India'
                        
                        # Extract description or stipend info
                        description = title
                        stipend_elem = card.find('p', class_=['stipend', 'salary'])
                        if stipend_elem:
                            description += f" - {stipend_elem.get_text(strip=True)}"
                        
                        link_elem = card.find('a', href=True)
                        url = link_elem['href'] if link_elem else f"{self.INTERNSHALA_API}/internships/"
                        if not url.startswith('http'):
                            url = f"{self.INTERNSHALA_API}{url}"
                        
                        job_id = url.split('/')[-1] if '/' in url else str(time.time())
                        
                        skills = self._extract_skills(f"{title} {company}")
                        
                        jobs.append(JobData(
                            job_id=f"internshala_{job_id}",
                            title=title,
                            company=company,
                            location=location,
                            description=description,
                            requirements=[],
                            skills=skills,
                            salary_min=None,
                            salary_max=None,
                            job_type='Internship',
                            posted_date='',
                            source='internshala',
                            url=url
                        ))
                    
                    except Exception as e:
                        print(f"Error parsing Internshala card: {e}")
                        continue
        
        except Exception as e:
            print(f"Error fetching from Internshala: {e}")
        
        return jobs
    
    def fetch_glassdoor_jobs(
        self,
        keyword: str,
        location: str = "United States",
        limit: int = 30
    ) -> List[JobData]:
        """Fetch jobs from Glassdoor using web scraping"""
        jobs = []
        
        try:
            # Glassdoor search URL
            search_query = keyword.replace(" ", "-")
            location_query = location.replace(" ", "-")
            search_url = f"{self.GLASSDOOR_API}/Job/jobs.htm?keyword={search_query}&location={location_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job listings - Glassdoor uses various class names
                job_listings = soup.find_all('div', class_=['jobCard', 'Job', 'jl'])
                
                for listing in job_listings[:limit]:
                    try:
                        # Extract job title
                        title_elem = listing.find('h3', class_=['jobTitle', 'title'])
                        if not title_elem:
                            title_elem = listing.find('a', class_='jobLink')
                        title = title_elem.get_text(strip=True) if title_elem else 'Job Opening'
                        
                        # Extract company
                        company_elem = listing.find('div', class_=['jobMeta', 'company', 'employer'])
                        if not company_elem:
                            company_elem = listing.find('p', class_='company')
                        company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
                        
                        # Extract location
                        location_elem = listing.find('div', class_=['location', 'jobLocation'])
                        if not location_elem:
                            location_elem = listing.find('span', class_='loc')
                        job_location = location_elem.get_text(strip=True) if location_elem else location
                        
                        # Extract job description/snippet
                        desc_elem = listing.find('div', class_=['description', 'jobSnippet'])
                        description = desc_elem.get_text(strip=True) if desc_elem else title
                        
                        # Get job URL
                        link_elem = listing.find('a', href=True)
                        url = link_elem['href'] if link_elem else f"{self.GLASSDOOR_API}/job-listings"
                        if not url.startswith('http'):
                            url = f"{self.GLASSDOOR_API}{url}"
                        
                        job_id = url.split('/')[-1] if '/' in url else str(time.time())
                        
                        skills = self._extract_skills(f"{title} {description}")
                        
                        jobs.append(JobData(
                            job_id=f"glassdoor_{job_id}",
                            title=title,
                            company=company,
                            location=job_location,
                            description=description[:1000],
                            requirements=[],
                            skills=skills,
                            salary_min=None,
                            salary_max=None,
                            job_type='Full-time',
                            posted_date='',
                            source='glassdoor',
                            url=url
                        ))
                    
                    except Exception as e:
                        print(f"Error parsing Glassdoor listing: {e}")
                        continue
        
        except Exception as e:
            print(f"Error fetching from Glassdoor: {e}")
        
        return jobs
    
    def fetch_jobs_by_keyword(
        self,
        keyword: str,
        location: str = "us",
        sources: List[str] = None,
        category: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        **kwargs: Any
    ) -> List[JobData]:
        """Fetch jobs from multiple sources"""
        if sources is None:
            sources = ['remotive', 'unstop', 'internshala', 'glassdoor']

        # Backward/forward compatibility for callers using older filter names.
        if category is None:
            category = kwargs.get('job_category') or kwargs.get('role_category')
        if state is None:
            state = kwargs.get('area') or kwargs.get('region') or kwargs.get('state_name')
        if district is None:
            district = kwargs.get('district_name') or kwargs.get('city') or kwargs.get('district')

        all_jobs = []
        normalized_keyword = self.normalize_multilingual_keyword(keyword)

        for source in sources:
            if source == 'remotive':
                jobs = self.fetch_remote_jobs(category=category, search=normalized_keyword, limit=30)
                all_jobs.extend(jobs)
            elif source == 'adzuna':
                jobs = self.fetch_adzuna_jobs(normalized_keyword, location)
                all_jobs.extend(jobs)
            elif source == 'unstop':
                jobs = self.fetch_unstop_jobs(normalized_keyword, limit=30)
                all_jobs.extend(jobs)
            elif source == 'internshala':
                jobs = self.fetch_internshala_jobs(normalized_keyword, limit=30)
                all_jobs.extend(jobs)
            elif source == 'glassdoor':
                jobs = self.fetch_glassdoor_jobs(normalized_keyword, location)
                all_jobs.extend(jobs)

            # Rate limiting
            time.sleep(1)

        all_jobs = self.filter_jobs(
            all_jobs,
            keyword=keyword,
            category=category,
            location=location,
            state=state,
            district=district
        )
        return all_jobs

    def normalize_multilingual_keyword(self, keyword: str) -> str:
        """Map common non-English role searches to a normalized English query."""
        query = (keyword or "").strip().lower()
        if not query:
            return "developer"

        normalized_terms = []
        seen_terms = set()

        for raw_term in re.split(r"[,/|]+|\s{2,}", query):
            term = raw_term.strip()
            if not term:
                continue

            mapped_term = term
            for canonical, variants in self.MULTILINGUAL_KEYWORDS.items():
                if term == canonical or term in variants:
                    mapped_term = canonical
                    break

            if mapped_term not in seen_terms:
                normalized_terms.append(mapped_term)
                seen_terms.add(mapped_term)

        if not normalized_terms:
            return query
        return " ".join(normalized_terms)

    def filter_jobs(
        self,
        jobs: List[JobData],
        keyword: str,
        category: Optional[str] = None,
        location: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None
    ) -> List[JobData]:
        """Filter jobs by query relevance, category, and supported geography."""
        normalized_keyword = self.normalize_multilingual_keyword(keyword)
        search_terms = [
            term for term in re.split(r"[\s,/|]+", normalized_keyword.lower())
            if len(term) > 1
        ]
        category_term = (category or "").strip().lower()
        location_key = (location or "").strip().lower()
        state_term = (state or "").strip().lower()
        district_term = (district or "").strip().lower()

        filtered_jobs = []
        for job in jobs:
            haystack = " ".join([
                job.title,
                job.company,
                job.location,
                job.description,
                " ".join(job.skills),
            ]).lower()

            if search_terms and not any(term in haystack for term in search_terms):
                continue

            if category_term and category_term not in haystack:
                continue

            if not self._matches_location(job.location, location_key, state_term, district_term):
                continue

            filtered_jobs.append(job)

        return filtered_jobs

    def _matches_location(
        self,
        job_location: str,
        location_key: str,
        state_term: str = "",
        district_term: str = ""
    ) -> bool:
        """Check whether a remote job supports the selected country, state, and district."""
        location_text = (job_location or "remote").lower()

        if state_term and state_term != "all" and state_term not in location_text:
            state_aliases = self.LOCATION_SYNONYMS.get(state_term, [])
            if not any(alias in location_text for alias in state_aliases):
                return False

        if district_term and district_term != "all" and district_term not in location_text:
            district_aliases = self.LOCATION_SYNONYMS.get(district_term, [])
            if not any(alias in location_text for alias in district_aliases):
                return False

        if not location_key or location_key == "global":
            return True

        aliases = self.LOCATION_SYNONYMS.get(location_key, [location_key])
        return any(alias in location_text for alias in aliases)
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from job description"""
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
            'go', 'rust', 'scala', 'kotlin', 'swift', 'php', 'sql', 'html', 'css',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'git',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'data analysis', 'data science', 'nlp', 'computer vision',
            'agile', 'scrum', 'jira', 'rest api', 'graphql', 'mongodb',
            'postgresql', 'mysql', 'redis', 'elasticsearch', 'tableau',
            'excel', 'powerpoint', 'word', 'communication', 'leadership'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills[:20]  # Limit to 20 skills
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements from job description"""
        requirements = []
        
        # Look for requirements section
        lines = text.split('\n')
        in_requirements = False
        
        for line in lines:
            line_lower = line.lower()
            
            if 'requirement' in line_lower or 'qualification' in line_lower:
                in_requirements = True
                continue
            
            if in_requirements and line.strip():
                if any(kw in line_lower for kw in ['benefit', 'responsibility', 'duty']):
                    break
                requirements.append(line.strip())
        
        return requirements[:10]  # Limit to 10
    
    def save_jobs_to_file(self, jobs: List[JobData], filepath: str):
        """Save jobs to JSON file"""
        job_dicts = []
        
        for job in jobs:
            job_dicts.append({
                'job_id': job.job_id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'requirements': job.requirements,
                'skills': job.skills,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'job_type': job.job_type,
                'posted_date': job.posted_date,
                'source': job.source,
                'url': job.url
            })
        
        with open(filepath, 'w') as f:
            json.dump(job_dicts, f, indent=2)
        
        print(f"Saved {len(jobs)} jobs to {filepath}")
    
    def load_jobs_from_file(self, filepath: str) -> List[JobData]:
        """Load jobs from JSON file"""
        with open(filepath, 'r') as f:
            job_dicts = json.load(f)
        
        jobs = []
        
        for jd in job_dicts:
            jobs.append(JobData(
                job_id=jd['job_id'],
                title=jd['title'],
                company=jd['company'],
                location=jd['location'],
                description=jd['description'],
                requirements=jd['requirements'],
                skills=jd['skills'],
                salary_min=jd.get('salary_min'),
                salary_max=jd.get('salary_max'),
                job_type=jd['job_type'],
                posted_date=jd['posted_date'],
                source=jd['source'],
                url=jd['url']
            ))
        
        return jobs


def fetch_jobs(keyword: str, location: str = "us") -> List[Dict]:
    """Convenience function to fetch jobs"""
    fetcher = JobDataFetcher()
    jobs = fetcher.fetch_jobs_by_keyword(keyword, location)
    
    return [
        {
            'job_id': job.job_id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'description': job.description[:500],
            'skills': job.skills,
            'job_type': job.job_type,
            'source': job.source,
            'url': job.url
        }
        for job in jobs
    ]


if __name__ == "__main__":
    print("Job Data Fetcher Module Loaded")
    fetcher = JobDataFetcher()
    print("Ready to fetch jobs!")
