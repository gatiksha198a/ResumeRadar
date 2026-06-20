"""
Enhanced Streamlit Dashboard for Resume Analyzer
Interactive UI for analyzing resumes and matching to jobs
"""

from pathlib import Path
import sys
import inspect

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Optional
from collections import Counter
import io
import json
import time
from datetime import datetime

# Ensure the project root is importable when Streamlit runs this file directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import our modules
from src.parser import ResumeParser
from src.matcher import SemanticMatcher
from src.skill_extractor import SkillExtractor
from src.classifier import ResumeClassifier, classify_resume
from src.decision_engine import DecisionEngine
from src.ats_checker import ATSChecker
from src.job_fetcher import JobDataFetcher
from src.credibility_checker import CredibilityChecker


# Page configuration
st.set_page_config(
    page_title="AI Resume Analyzer Pro",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'AI Resume Analyzer - Hiring Intelligence Platform'
    }
)


# Custom CSS - Modern attractive design with premium effects
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg: #f0f5ff;
        --bg-secondary: #e8f0ff;
        --surface: rgba(255, 255, 255, 0.92);
        --surface-strong: #ffffff;
        --text: #0f172a;
        --text-secondary: #475569;
        --muted: #64748b;
        --line: rgba(148, 163, 184, 0.16);
        --brand: #3b82f6;
        --brand-secondary: #2563eb;
        --accent: #8b5cf6;
        --accent-light: #a78bfa;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --teal: #06b6d4;
        --rose: #ec4899;
        --shadow: 0 20px 60px rgba(59, 130, 246, 0.15);
        --shadow-lg: 0 30px 90px rgba(59, 130, 246, 0.25);
    }
    
    * { font-family: 'Poppins', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #f0f5ff 0%, #e8f0ff 25%, #f3f0ff 50%, #fef3ff 75%, #f0f5ff 100%);
        background-attachment: fixed;
        color: var(--text);
    }
    
    .stApp [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    }
    .stApp [data-testid="stSidebar"] * {
        color: #f8fafc;
    }
    .stApp [data-testid="stSidebar"] .stSelectbox label,
    .stApp [data-testid="stSidebar"] .stRadio label {
        color: #e2e8f0 !important;
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, rgba(248, 250, 255, 0.95), rgba(255, 255, 255, 0.98));
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    }
    [data-testid="stToolbar"] {
        right: 1rem;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 255, 0.92) 100%);
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        border-radius: 20px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.08);
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.12);
        animation: glow 1.5s ease-in-out infinite;
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }
    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.6rem;
        font-weight: 700;
        letter-spacing: -0.06em;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: left;
        margin-bottom: 0.8rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .sub-header {
        font-family: 'Poppins', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 1.5rem;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-shell {
        position: relative;
        overflow: hidden;
        border-radius: 32px;
        padding: 40px 40px 32px;
        margin-bottom: 28px;
        border: 1.5px solid rgba(148, 163, 184, 0.2);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 255, 0.92) 100%);
        box-shadow: var(--shadow-lg);
        backdrop-filter: blur(20px);
        animation: slideInUp 0.8s ease-out, float 4s ease-in-out infinite;
        animation-delay: 0s, 0.8s;
    }
    .hero-shell::after {
        content: "";
        position: absolute;
        inset: auto -40px -55px auto;
        width: 180px;
        height: 180px;
        background: radial-gradient(circle, rgba(15, 118, 110, 0.22), transparent 65%);
        pointer-events: none;
    }
    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 18px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 255, 0.92));
        border: 1.5px solid rgba(148, 163, 184, 0.2);
        color: #3b82f6;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    .hero-copy {
        max-width: 760px;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #475569;
        margin: 1rem 0 1.2rem;
        font-weight: 500;
    }
    .hero-stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin-top: 22px;
    }
    .hero-stat {
        padding: 18px 20px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.8);
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
        transition: all 0.3s ease;
    }
    .hero-stat:hover {
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.12);
        transform: translateY(-2px);
    }
    .hero-stat strong {
        display: block;
        font-family: 'Poppins', sans-serif;
        font-size: 1.3rem;
        color: #0f172a;
        font-weight: 700;
    }
    .hero-stat span {
        color: #64748b;
        font-size: 0.88rem;
        line-height: 1.5;
    }
    .hero-shell p,
    .hero-shell span,
    .hero-shell strong {
        color: inherit;
    }
    .signal-ribbon {
        display: grid;
        grid-template-columns: 1.2fr 1fr 1fr;
        gap: 14px;
        margin: 0 0 22px;
    }
    .signal-panel {
        border-radius: 22px;
        padding: 20px 22px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 255, 0.92) 100%);
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.1);
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
    }
    .signal-panel:hover {
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px);
        animation: glow 1.5s ease-in-out infinite;
    }
    .signal-panel strong {
        display: block;
        font-family: 'Poppins', sans-serif;
        font-size: 1.05rem;
        color: #0f172a;
        margin-bottom: 8px;
        font-weight: 700;
    }
    .signal-panel span {
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .card h1, .card h2, .card h3, .card h4, .card strong,
    .signature-card h3, .signal-panel strong, .hero-stat strong,
    .stack-copy strong, .sub-header, .main-header {
        color: var(--text) !important;
    }
    .card p, .card span, .signature-card p, .signal-panel span,
    .hero-copy, .hero-stat span, .stack-copy span,
    .stMarkdown, [data-testid="stMetricLabel"], label {
        color: var(--muted);
    }
    .signature-grid {
        display: grid;
        grid-template-columns: 1.35fr 0.95fr;
        gap: 18px;
        margin-bottom: 22px;
    }
    .signature-card {
        min-height: 220px;
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.1);
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        transition: all 0.3s ease;
        animation: slideInUp 0.7s ease-out;
    }
    .signature-card:hover {
        box-shadow: 0 15px 50px rgba(59, 130, 246, 0.15);
        transform: translateY(-4px);
        animation: glow 1.5s ease-in-out infinite;
    }
    .signature-story {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 255, 0.92) 100%);
    }
    .signature-story h3,
    .signature-stack h3 {
        font-family: 'Poppins', sans-serif;
        font-size: 1.4rem;
        color: #0f172a;
        margin-bottom: 12px;
        font-weight: 700;
    }
    .signature-story p,
    .signature-stack p {
        color: #475569;
        line-height: 1.75;
        font-weight: 500;
    }
    .signature-stack {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 255, 0.92) 100%);
    }
    .stack-item {
        display: flex;
        gap: 14px;
        align-items: flex-start;
        padding: 14px 0;
        border-top: 1px solid rgba(148, 163, 184, 0.12);
        transition: all 0.3s ease;
    }
    .stack-item:hover {
        padding-left: 2px;
    }
    .stack-item:first-of-type {
        border-top: none;
    }
    .stack-index {
        min-width: 36px;
        height: 36px;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        flex-shrink: 0;
    }
    .stack-copy strong {
        display: block;
        color: #0f172a;
        margin-bottom: 4px;
        font-weight: 700;
    }
    .stack-copy span {
        color: #64748b;
        font-size: 0.92rem;
        line-height: 1.6;
    }
    .pulse-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 16px 0 18px;
    }
    .pulse-card {
        border-radius: 20px;
        padding: 20px 22px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 255, 0.92) 100%);
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.1);
        transition: all 0.3s ease;
        animation: fadeIn 0.7s ease-out;
    }
    .pulse-card:hover {
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px) scale(1.01);
        animation: glow 1.5s ease-in-out infinite;
    }
    .pulse-card strong {
        display: block;
        font-family: 'Poppins', sans-serif;
        font-size: 1.25rem;
        color: #0f172a;
        margin-bottom: 8px;
        font-weight: 700;
    }
    .pulse-card span {
        color: #64748b;
        line-height: 1.6;
        font-size: 0.92rem;
    }
    .card {
        background: rgba(255, 255, 255, 0.96);
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(148, 163, 184, 0.12);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: fadeIn 0.7s ease-out;
    }
    .card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.2), transparent);
    }
    .card:hover {
        box-shadow: 0 20px 60px rgba(59, 130, 246, 0.2);
        transform: translateY(-6px);
        border-color: rgba(148, 163, 184, 0.25);
        animation: glow 2s ease-in-out infinite;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 255, 0.92) 100%);
        border-radius: 22px;
        padding: 24px;
        text-align: center;
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.1);
        transition: all 0.3s ease;
        animation: fadeIn 0.7s ease-out;
    }
    .metric-card:hover {
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px) scale(1.02);
        animation: glow 1.5s ease-in-out infinite;
    }
    .metric-value { 
        font-size: 2.8rem; 
        font-weight: 700; 
        color: #3b82f6;
        font-family: 'Space Grotesk', sans-serif;
    }
    .metric-label { 
        font-size: 0.95rem; 
        color: #64748b; 
        margin-top: 10px;
        font-weight: 500;
    }
    .decision-badge {
        padding: 14px 28px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.15rem;
        display: inline-block;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15);
        text-transform: uppercase;
        letter-spacing: 1px;
        animation: scaleIn 0.5s ease-out, pulse 2s ease-in-out infinite;
        animation-delay: 0s, 0.5s;
        transition: all 0.3s ease;
    }
    .decision-hire { 
        background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
        color: white;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
    }
    .decision-hire:hover { 
        box-shadow: 0 15px 40px rgba(16, 185, 129, 0.4);
        transform: scale(1.05);
    }
    .decision-shortlist { 
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
        color: white;
        box-shadow: 0 10px 30px rgba(245, 158, 11, 0.3);
    }
    .decision-shortlist:hover { 
        box-shadow: 0 15px 40px rgba(245, 158, 11, 0.4);
        transform: scale(1.05);
    }
    .decision-reject { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
        color: white;
        box-shadow: 0 10px 30px rgba(239, 68, 68, 0.3);
    }
    .decision-reject:hover { 
        box-shadow: 0 15px 40px rgba(239, 68, 68, 0.4);
        transform: scale(1.05);
    }
    .skill-tag {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 0.85rem;
        margin: 6px 4px;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        animation: slideInUp 0.5s ease-out;
    }
    .skill-tag:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
        animation: float 2s ease-in-out infinite;
    }
    .skill-matched { 
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        color: #065f46;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .skill-missing { 
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #991b1b;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    @keyframes fadeIn { 
        from { opacity: 0; transform: translateY(15px); } 
        to { opacity: 1; transform: translateY(0); } 
    }
    @keyframes slideInLeft { 
        from { opacity: 0; transform: translateX(-30px); } 
        to { opacity: 1; transform: translateX(0); } 
    }
    @keyframes slideInRight { 
        from { opacity: 0; transform: translateX(30px); } 
        to { opacity: 1; transform: translateX(0); } 
    }
    @keyframes slideInUp { 
        from { opacity: 0; transform: translateY(30px); } 
        to { opacity: 1; transform: translateY(0); } 
    }
    @keyframes scaleIn { 
        from { opacity: 0; transform: scale(0.95); } 
        to { opacity: 1; transform: scale(1); } 
    }
    @keyframes pulse { 
        0%, 100% { opacity: 1; transform: scale(1); } 
        50% { opacity: 0.85; transform: scale(1.02); } 
    }
    @keyframes float { 
        0%, 100% { transform: translateY(0px); } 
        50% { transform: translateY(-8px); } 
    }
    @keyframes glow { 
        0%, 100% { box-shadow: 0 8px 24px rgba(59, 130, 246, 0.08); } 
        50% { box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15); } 
    }
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    @keyframes bounce { 
        0%, 100% { transform: translateY(0); } 
        50% { transform: translateY(-10px); } 
    }
    @keyframes spin { 
        from { transform: rotate(0deg); } 
        to { transform: rotate(360deg); } 
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); max-height: 0; }
        to { opacity: 1; transform: translateY(0); max-height: 500px; }
    }
    .fade-in { animation: fadeIn 0.6s ease-out; }
    .slide-in { animation: slideInLeft 0.6s ease-out; }
    .slide-in-right { animation: slideInRight 0.6s ease-out; }
    .slide-in-up { animation: slideInUp 0.7s ease-out; }
    .scale-in { animation: scaleIn 0.5s ease-out; }
    .pulse-animation { animation: pulse 2.5s ease-in-out infinite; }
    .float-animation { animation: float 3s ease-in-out infinite; }
    .glow-animation { animation: glow 2s ease-in-out infinite; }
    .bounce-animation { animation: bounce 1s ease-in-out infinite; }
    .spin-animation { animation: spin 1s linear infinite; }
    .slide-down-animation { animation: slideDown 0.5s ease-out; }
    .shimmer-animation { 
        background: linear-gradient(90deg, #f0f5ff 25%, #e8f0ff 50%, #f0f5ff 75%);
        background-size: 1000px 100%;
        animation: shimmer 2s infinite;
    }
    .stButton > button {
        border-radius: 18px;
        font-weight: 700;
        padding: 14px 32px;
        border: none;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.3px;
        font-size: 0.95rem;
        animation: slideInUp 0.6s ease-out;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        animation: none;
    }
    .stButton > button:active {
        transform: translateY(-1px);
        animation: bounce 0.4s ease;
    }
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {
        border-radius: 18px !important;
        background: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid rgba(148, 163, 184, 0.2) !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
        transition: all 0.3s ease !important;
        font-size: 0.95rem;
        animation: slideInUp 0.5s ease-out;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus,
    .stSelectbox [data-baseweb="select"] > div:focus,
    .stMultiSelect [data-baseweb="select"] > div:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1), inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
        animation: glow 1.5s ease-in-out infinite;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(248, 250, 255, 0.8);
        padding: 12px;
        border-radius: 20px;
        border: 1px solid rgba(148, 163, 184, 0.15);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
        animation: slideInUp 0.6s ease-out;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 14px;
        font-weight: 600;
        color: #64748b;
        transition: all 0.3s ease;
        padding: 10px 20px;
        animation: fadeIn 0.5s ease-out;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(59, 130, 246, 0.05);
        transform: translateY(-1px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1)) !important;
        color: #3b82f6 !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        animation: slideInDown 0.3s ease-out;
    }
    .stProgress > div > div > div { 
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        animation: shimmer 2s infinite;
    }
    div[data-testid="stExpander"] {
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.12);
        animation: glow 1.5s ease-in-out infinite;
    }
    .glass-note {
        padding: 18px 20px;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(248, 250, 255, 0.95), rgba(255, 255, 255, 0.92));
        border: 1.5px solid rgba(148, 163, 184, 0.15);
        color: #475569;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
        font-weight: 500;
    }
    .stSuccess { background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 16px; }
    .stError { background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-radius: 16px; }
    .stWarning { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 16px; }
    .stInfo { background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 16px; }
    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-track { background: rgba(148, 163, 184, 0.1); }
    ::-webkit-scrollbar-thumb { 
        background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 100%);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover { 
        background: linear-gradient(180deg, #2563eb 0%, #7c3aed 100%);
    }
    @media (max-width: 900px) {
        .main-header {
            font-size: 2.5rem;
            text-align: left;
        }
        .hero-shell {
            padding: 24px 20px;
        }
        .hero-stats {
            grid-template-columns: 1fr;
        }
        .signal-ribbon,
        .signature-grid,
        .pulse-grid {
            grid-template-columns: 1fr;
        }
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg: #07111f;
            --surface: rgba(10, 18, 30, 0.82);
            --surface-strong: #101826;
            --text: #eef4ff;
            --muted: #b8c4d8;
            --line: rgba(148, 163, 184, 0.18);
            --brand: #f59e0b;
            --brand-deep: #fb923c;
            --teal: #2dd4bf;
            --rose: #fb7185;
            --shadow: 0 24px 60px rgba(2, 8, 23, 0.42);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(245, 158, 11, 0.14), transparent 26%),
                radial-gradient(circle at top right, rgba(45, 212, 191, 0.10), transparent 24%),
                linear-gradient(180deg, #020617 0%, #0b1220 52%, #111827 100%);
            color: var(--text);
        }
        .stApp [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(2, 6, 23, 0.98) 0%, rgba(15, 23, 42, 0.98) 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.14);
        }
        [data-testid="stHeader"] {
            background: rgba(2, 6, 23, 0.74);
        }
        [data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.14);
            box-shadow: 0 12px 30px rgba(2, 8, 23, 0.34);
        }
        .hero-shell,
        .hero-stat,
        .hero-kicker,
        .signature-story,
        .signature-stack,
        .signal-panel,
        .card,
        div[data-testid="stExpander"],
        .glass-note {
            background:
                linear-gradient(135deg, rgba(10, 18, 30, 0.92), rgba(15, 23, 42, 0.84)) !important;
            border-color: rgba(148, 163, 184, 0.14) !important;
        }
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            background: rgba(15, 23, 42, 0.94) !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            color: var(--text) !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.10);
        }
        .stTabs [data-baseweb="tab"] {
            color: #dbe5f3;
        }
        .stTabs [aria-selected="true"] {
            color: white !important;
        }
        .hero-kicker {
            background: rgba(255, 255, 255, 0.10) !important;
            color: #ffd39a !important;
            border-color: rgba(251, 146, 60, 0.28) !important;
        }
        .hero-stat {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(148, 163, 184, 0.16) !important;
            box-shadow: none !important;
        }
        .hero-stat strong,
        .hero-stat span,
        .hero-copy,
        .hero-shell .main-header {
            color: var(--text) !important;
        }
        .hero-copy,
        .hero-stat span {
            color: var(--muted) !important;
        }
        .card p, .card span, .signature-card p, .signal-panel span,
        .hero-copy, .hero-stat span, .stack-copy span,
        .stMarkdown, [data-testid="stMetricLabel"], label {
            color: var(--muted) !important;
        }
        .card h1, .card h2, .card h3, .card h4, .card strong,
        .signature-card h3, .signal-panel strong, .hero-stat strong,
        .pulse-card strong,
        .stack-copy strong, .sub-header {
            color: var(--text) !important;
        }
        .pulse-card {
            background: linear-gradient(135deg, rgba(10, 18, 30, 0.92), rgba(15, 23, 42, 0.86)) !important;
            border-color: rgba(148, 163, 184, 0.14) !important;
        }
        .pulse-card span {
            color: var(--muted) !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = None
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'page' not in st.session_state:
    st.session_state.page = "Home"


def parse_uploaded_file(uploaded_file) -> Dict:
    parser = ResumeParser()
    content = uploaded_file.read()
    parsed = parser.parse_file(content, uploaded_file.name)
    return parser.to_dict(parsed)


def analyze_resume(resume_data: Dict, job_description: str, required_skills: List[str] = None):
    results = {}
    
    # 1. Semantic matching
    matcher = SemanticMatcher()
    match_result = matcher.match_resume_to_job(resume_data, job_description, required_skills)
    results['match'] = {
        'overall_score': match_result.overall_score,
        'skills_score': match_result.skills_score,
        'experience_score': match_result.experience_score,
        'summary_score': match_result.summary_score,
        'matched_skills': match_result.matched_skills,
        'missing_skills': match_result.missing_skills
    }
    
    # 2. Hiring decision
    decision_engine = DecisionEngine()
    decision = decision_engine.decide(results['match'], resume_data)
    results['decision'] = {
        'decision': decision.decision,
        'confidence': decision.confidence,
        'reasons': decision.reasons,
        'recommendations': decision.recommendations
    }
    
    # 3. ATS check
    ats_checker = ATSChecker()
    ats_result = ats_checker.check_resume(resume_data, job_description)
    results['ats'] = {
        'score': ats_result.score,
        'issues': ats_result.issues,
        'suggestions': ats_result.suggestions,
        'section_analysis': ats_result.section_analysis
    }
    
    # 4. Skill extraction
    skill_extractor = SkillExtractor()
    skills_result = skill_extractor.extract_skills(resume_data.get('raw_text', ''))
    results['skills'] = {
        'categories': {k: {'skills': v.skills, 'level': v.level} for k, v in skills_result.items()},
        'all_skills': skill_extractor.extract_tech_stack(resume_data.get('raw_text', ''))
    }
    
    # 5. Classification
    classification = classify_resume(resume_data)
    results['classification'] = classification
    
    # 6. Additional analysis
    credibility_checker = CredibilityChecker()
    credibility = credibility_checker.analyze(resume_data, job_description)
    results['credibility'] = credibility.to_dict()

    # 7. Additional analysis
    results['additional'] = generate_additional_insights(resume_data, job_description, results)
    
    return results


def generate_additional_insights(resume_data: Dict, job_description: str, results: Dict) -> Dict:
    insights = {}
    
    # Salary estimation
    skills = results['skills']['all_skills']
    experience_years = len(resume_data.get('experience', [])) * 2
    base_salary = 50000
    skill_bonus = len(skills) * 2000
    exp_bonus = experience_years * 3000
    
    insights['estimated_salary'] = {
        'min': base_salary + skill_bonus + exp_bonus - 15000,
        'max': base_salary + skill_bonus + exp_bonus + 15000,
        'currency': 'USD'
    }
    
    insights['interview_questions'] = generate_interview_questions(results)
    insights['learning_resources'] = generate_learning_resources(results['match']['missing_skills'])
    
    insights['strengths'] = []
    insights['weaknesses'] = []
    
    if results['match']['overall_score'] > 75:
        insights['strengths'].append("Strong overall match with job requirements")
    if results['ats']['score'] > 80:
        insights['strengths'].append("Excellent ATS compatibility")
    if results['credibility']['overall_score'] > 75:
        insights['strengths'].append("Strong credibility signals across skills, experience, and portfolio proof")
    if len(results['match']['matched_skills']) > 5:
        insights['strengths'].append("Good technical skill coverage")
        
    if results['ats']['score'] < 60:
        insights['weaknesses'].append("Poor ATS compatibility - fix formatting issues")
    if len(results['match']['missing_skills']) > 3:
        insights['weaknesses'].append("Missing key skills required for the role")
    if results['match']['experience_score'] < 50:
        insights['weaknesses'].append("Experience section needs improvement")
    if results['credibility']['flags']:
        insights['weaknesses'].append("Credibility review flagged claims that need manual verification")
    
    return insights


def generate_interview_questions(results: Dict) -> List[Dict]:
    questions = []
    matched_skills = results['match']['matched_skills']
    
    general_questions = [
        {"question": "Tell me about yourself and your background", "category": "General"},
        {"question": "What interests you about this role?", "category": "General"},
        {"question": "Where do you see yourself in 5 years?", "category": "General"},
    ]
    questions.extend(general_questions)
    
    skill_questions = {
        "python": "Describe a complex Python project you've worked on",
        "javascript": "Explain the difference between var, let, and const",
        "sql": "How would you optimize a slow SQL query?",
        "machine learning": "Explain the difference between supervised and unsupervised learning",
        "aws": "How would you design a scalable architecture on AWS?",
        "docker": "Explain the benefits of containerization with Docker",
        "react": "What is the virtual DOM and how does it work?",
        "data analysis": "Describe your process for analyzing a large dataset",
    }
    
    for skill in matched_skills:
        skill_lower = skill.lower()
        for key, question in skill_questions.items():
            if key in skill_lower:
                questions.append({"question": question, "category": "Technical"})
                break
    
    return questions[:10]


def generate_learning_resources(missing_skills: List[str]) -> Dict:
    resources = {}
    
    skill_resources = {
        "python": {"courses": ["Python for Everybody (Coursera)", "Real Python"], "youtube": ["Corey Schafer", "Tech With Tim"]},
        "javascript": {"courses": ["JavaScript: The Complete Guide (Udemy)", "freeCodeCamp"], "youtube": ["Traversy Media", "JavaScript Mastery"]},
        "react": {"courses": ["React - The Complete Guide", "React Docs"], "youtube": ["JavaScript Mastery", "Sonny Sangha"]},
        "aws": {"courses": ["AWS Solutions Architect (A Cloud Guru)", "AWS Free Tier"], "youtube": ["AWS Training by Adam Smith"]},
        "docker": {"courses": ["Docker for Beginners", "Docker Mastery"], "youtube": ["Techworld with Nana"]},
        "sql": {"courses": ["SQL for Data Science (Coursera)", "Mode Analytics SQL Tutorial"], "youtube": ["Alex the Analyst"]},
        "machine learning": {"courses": ["Machine Learning by Andrew Ng", "Fast.ai"], "youtube": ["3Blue1Brown", "Sentdex"]},
        "data science": {"courses": ["IBM Data Science Professional Certificate", "Kaggle Courses"], "youtube": ["Kenny Moss"]},
        "git": {"courses": ["Git Complete (Udemy)", "Atlassian Git Tutorial"], "youtube": ["Traversy Media"]},
        "agile": {"courses": ["Agile Project Management (Coursera)", "Scrum Guide"], "youtube": ["Agile Academy"]},
    }
    
    for skill in missing_skills:
        skill_lower = skill.lower()
        for key, res in skill_resources.items():
            if key in skill_lower:
                resources[skill] = res
                break
        else:
            resources[skill] = {"courses": [f"Online courses for {skill}"], "youtube": [f"{skill} tutorials"]}
    
    return resources


def create_gauge_chart(score: float, title: str, color: str = None) -> go.Figure:
    if color is None:
        if score >= 75: color = "#10b981"
        elif score >= 50: color = "#f59e0b"
        else: color = "#ef4444"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title, 'font': {'size': 16, 'color': '#1e293b'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
            'bar': {'color': color, 'thickness': 0.7},
            'bgcolor': "#f1f5f9",
            'steps': [
                {'range': [0, 50], 'color': "#fee2e2"},
                {'range': [50, 75], 'color': "#fef3c7"},
                {'range': [75, 100], 'color': "#d1fae5"}
            ],
            'threshold': {'line': {'color': "#1e293b", 'width': 2}, 'thickness': 0.8, 'value': 75}
        },
        number={'font': {'size': 28, 'color': color}}
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'family': 'Inter'})
    return fig


def create_radar_chart(scores: Dict, title: str = "Score Breakdown") -> go.Figure:
    categories = list(scores.keys())
    values = list(scores.values())
    categories = categories + [categories[0]]
    values = values + [values[0]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        fillcolor='rgba(102, 126, 234, 0.3)',
        line=dict(color='#667eea', width=2), name='Scores'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickcolor="#64748b", tickfont=dict(color="#64748b")), bgcolor='rgba(0,0,0,0)'),
        showlegend=False, height=350, paper_bgcolor='rgba(0,0,0,0)', font={'family': 'Inter'}
    )
    return fig


def create_skill_pie_chart(matched: List[str], missing: List[str]) -> go.Figure:
    labels = ['Matched Skills', 'Missing Skills']
    values = [len(matched), len(missing)]
    colors = ['#10b981', '#ef4444']
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5, marker=dict(colors=colors), textinfo='label+percent', textfont=dict(size=12))])
    fig.update_layout(height=300, showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font={'family': 'Inter'})
    return fig


def create_score_history_chart(history: List[Dict]) -> go.Figure:
    if not history:
        return None
    df = pd.DataFrame(history)
    fig = px.line(df, x='timestamp', y='score', markers=True, title="Analysis History")
    fig.update_traces(line_color='#667eea', marker=dict(size=10))
    fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'family': 'Inter'})
    return fig


def extract_metro_label(location: str) -> str:
    location_text = (location or "").lower()
    metro_aliases = {
        "Bengaluru": ["bengaluru", "bangalore"],
        "Mumbai": ["mumbai", "navi mumbai", "thane"],
        "Delhi NCR": ["new delhi", "delhi", "gurugram", "gurgaon", "noida", "faridabad"],
        "Hyderabad": ["hyderabad"],
        "Chennai": ["chennai"],
        "Pune": ["pune"],
        "Kolkata": ["kolkata", "calcutta"],
        "Ahmedabad": ["ahmedabad", "gandhinagar"],
        "San Francisco Bay Area": ["san francisco", "oakland", "san jose", "bay area"],
        "New York Metro": ["new york city", "new york", "brooklyn", "queens", "jersey city"],
        "Seattle": ["seattle", "bellevue", "redmond"],
        "Los Angeles": ["los angeles", "anaheim", "long beach"],
        "Toronto": ["toronto", "mississauga", "brampton"],
        "Vancouver": ["vancouver", "surrey", "burnaby"],
        "London": ["london"],
        "Manchester": ["manchester"],
        "Sydney": ["sydney"],
        "Melbourne": ["melbourne"],
        "Remote / Global": ["remote", "worldwide", "global", "anywhere"],
    }

    for metro, aliases in metro_aliases.items():
        if any(alias in location_text for alias in aliases):
            return metro
    return "Other Metros"


def build_market_pulse(jobs: List) -> Dict[str, str]:
    if not jobs:
        return {
            "top_metro": "No metro data yet",
            "remote_share": "0%",
            "top_skill": "No skill trend",
        }

    metro_counter = Counter()
    skill_counter = Counter()
    remote_jobs = 0

    for job in jobs:
        metro_counter[extract_metro_label(job.location)] += 1
        if "remote" in (job.location or "").lower() or "remote" in (job.job_type or "").lower():
            remote_jobs += 1
        for skill in job.skills[:8]:
            skill_counter[skill] += 1

    top_metro, top_metro_count = metro_counter.most_common(1)[0]
    top_skill = skill_counter.most_common(1)[0][0] if skill_counter else "Generalist roles"
    remote_share = f"{round((remote_jobs / max(len(jobs), 1)) * 100)}%"

    return {
        "top_metro": f"{top_metro} ({top_metro_count} jobs)",
        "remote_share": remote_share,
        "top_skill": top_skill,
    }


def get_location_aliases() -> Dict[str, List[str]]:
    return {
        "in": ["india", "ind", "remote india"],
        "us": ["united states", "usa", "us", "u.s.", "america", "remote us"],
        "uk": ["united kingdom", "uk", "u.k.", "britain", "england", "remote uk"],
        "ca": ["canada", "ca", "remote canada"],
        "au": ["australia", "au", "remote australia"],
        "delhi ncr": ["delhi ncr", "new delhi", "gurugram", "gurgaon", "noida", "faridabad", "ghaziabad"],
        "karnataka": ["karnataka", "bengaluru", "bangalore", "mysuru", "mangaluru", "hubballi"],
        "maharashtra": ["maharashtra", "mumbai", "pune", "nagpur", "thane", "navi mumbai"],
        "tamil nadu": ["tamil nadu", "chennai", "coimbatore", "madurai", "tiruchirappalli"],
        "telangana": ["telangana", "hyderabad", "warangal", "nizamabad", "karimnagar"],
        "west bengal": ["west bengal", "kolkata", "howrah", "siliguri", "durgapur"],
        "gujarat": ["gujarat", "ahmedabad", "surat", "vadodara", "rajkot", "gandhinagar"],
        "kerala": ["kerala", "kochi", "cochin", "thiruvananthapuram", "kozhikode", "thrissur"],
        "new delhi": ["new delhi", "delhi"],
        "gurugram": ["gurugram", "gurgaon"],
        "noida": ["noida"],
        "faridabad": ["faridabad"],
        "ghaziabad": ["ghaziabad"],
        "bengaluru urban": ["bengaluru urban", "bengaluru", "bangalore"],
        "mysuru": ["mysuru", "mysore"],
        "mangaluru": ["mangaluru", "mangalore"],
        "hubballi": ["hubballi", "hubli"],
        "mumbai": ["mumbai"],
        "pune": ["pune"],
        "nagpur": ["nagpur"],
        "navi mumbai": ["navi mumbai"],
        "thane": ["thane"],
        "chennai": ["chennai"],
        "coimbatore": ["coimbatore"],
        "madurai": ["madurai"],
        "tiruchirappalli": ["tiruchirappalli", "trichy"],
        "hyderabad": ["hyderabad"],
        "warangal": ["warangal"],
        "nizamabad": ["nizamabad"],
        "karimnagar": ["karimnagar"],
        "kolkata": ["kolkata", "calcutta"],
        "howrah": ["howrah"],
        "siliguri": ["siliguri"],
        "durgapur": ["durgapur"],
        "ahmedabad": ["ahmedabad"],
        "surat": ["surat"],
        "vadodara": ["vadodara", "baroda"],
        "rajkot": ["rajkot"],
        "kochi": ["kochi", "cochin"],
        "thiruvananthapuram": ["thiruvananthapuram", "trivandrum"],
        "kozhikode": ["kozhikode", "calicut"],
        "thrissur": ["thrissur", "trichur"],
    }


def location_matches_filters(location_text: str, country: str, state: Optional[str], district: Optional[str]) -> bool:
    aliases = get_location_aliases()
    location_value = (location_text or "").lower()

    if country and country != "global":
        country_aliases = aliases.get(country, [country])
        if not any(alias in location_value for alias in country_aliases):
            return False

    if state:
        state_key = state.strip().lower()
        state_aliases = aliases.get(state_key, [state_key])
        if not any(alias in location_value for alias in state_aliases):
            return False

    if district:
        district_key = district.strip().lower()
        district_aliases = aliases.get(district_key, [district_key])
        if not any(alias in location_value for alias in district_aliases):
            return False

    return True


def fetch_jobs_for_search(
    fetcher: JobDataFetcher,
    keyword: str,
    location: str,
    category: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> List:
    """Call the fetcher in a way that remains compatible with older loaded versions."""
    method = fetcher.fetch_jobs_by_keyword
    signature = inspect.signature(method)
    supported = signature.parameters

    call_kwargs = {
        "keyword": keyword,
        "location": location,
        "sources": ["remotive", "unstop", "internshala", "glassdoor"],
    }
    if "category" in supported:
        call_kwargs["category"] = category
    if "state" in supported:
        call_kwargs["state"] = state
    elif "area" in supported:
        call_kwargs["area"] = state
    if "district" in supported:
        call_kwargs["district"] = district

    jobs = method(**call_kwargs)

    # Fallback filtering for older fetcher versions that don't understand newer filters.
    filtered_jobs = []
    category_term = (category or "").strip().lower()
    state_term = (state or "").strip().lower()
    district_term = (district or "").strip().lower()

    for job in jobs:
        job_location = getattr(job, "location", "")
        haystack = " ".join([
            getattr(job, "title", ""),
            getattr(job, "company", ""),
            job_location,
            getattr(job, "description", ""),
            " ".join(getattr(job, "skills", [])),
        ]).lower()

        if category_term and category_term not in haystack:
            continue
        if not location_matches_filters(
            location_text=job_location,
            country=location,
            state=state,
            district=district,
        ):
            continue
        filtered_jobs.append(job)

    return filtered_jobs


def display_candidate_card(results: Dict, resume_data: Dict, rank: int = 1):
    decision = results['decision']['decision']
    score = results['match']['overall_score']
    
    if decision == 'Hire':
        color, badge_class = '#10b981', 'decision-hire'
    elif decision == 'Shortlist':
        color, badge_class = '#f59e0b', 'decision-shortlist'
    else:
        color, badge_class = '#ef4444', 'decision-reject'
    
    with st.container():
        st.markdown(f"""
        <div class="card fade-in">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: #1e293b;">#{rank} {resume_data.get('name', 'Unknown Candidate')}</h3>
                    <p style="margin: 5px 0; color: #64748b;">{resume_data.get('email', 'N/A')} | {resume_data.get('phone', 'N/A')}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2rem; font-weight: 700; color: {color};">{score:.1f}%</div>
                    <span class="decision-badge {badge_class}">{decision}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def export_to_csv(results: Dict, resume_data: Dict) -> str:
    data = {
        'Field': ['Name', 'Email', 'Phone', 'GitHub', 'Overall Score', 'Skills Score', 'Experience Score', 'ATS Score', 'Credibility Score', 'Decision', 'Confidence', 'Matched Skills', 'Missing Skills'],
        'Value': [
            resume_data.get('name', 'N/A'), resume_data.get('email', 'N/A'), resume_data.get('phone', 'N/A'), resume_data.get('github', 'N/A'),
            results['match']['overall_score'], results['match']['skills_score'], results['match']['experience_score'],
            results['ats']['score'], results['credibility']['overall_score'], results['decision']['decision'], results['decision']['confidence'],
            ', '.join(results['match']['matched_skills']), ', '.join(results['match']['missing_skills'])
        ]
    }
    df = pd.DataFrame(data)
    return df.to_csv(index=False)


def main():
    # Header
    st.markdown('''
    <div class="hero-shell fade-in">
        <span class="hero-kicker">AI Hiring Workspace</span>
        <p class="main-header">AI Resume Analyzer Pro</p>
        <p class="hero-copy">Review resumes, rank candidates, and surface ATS issues inside a cleaner hiring dashboard built for faster screening and sharper decisions.</p>
        <div class="hero-stats">
            <div class="hero-stat">
                <strong>Resume Intelligence</strong>
                <span>Structured parsing, skill extraction, and match scoring</span>
            </div>
            <div class="hero-stat">
                <strong>Hiring Signals</strong>
                <span>Decision support, ATS checks, and candidate comparisons</span>
            </div>
            <div class="hero-stat">
                <strong>Job Discovery</strong>
                <span>Area-aware search with multilingual keyword support</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        st.markdown("### Menu")
        page = st.radio("Select Mode", ["Home", "Single Analysis", "Batch Ranking", "Job Search", "ATS Checker", "History"])
        st.divider()
        st.markdown("### Quick Stats")
        if st.session_state.history:
            st.metric("Total Analyses", len(st.session_state.history))
            avg_score = sum(h['score'] for h in st.session_state.history) / len(st.session_state.history)
            st.metric("Avg Score", f"{avg_score:.1f}%")
        st.divider()
        st.info("**Pro Tips:** Use clear resumes, include job keywords, quantify achievements, and keep resumes under 2 pages.")
    
    # Route to appropriate page
    if page == "Home":
        home_page()
    elif page == "Single Analysis":
        single_resume_analysis()
    elif page == "Batch Ranking":
        batch_ranking()
    elif page == "Job Search":
        job_search()
    elif page == "ATS Checker":
        ats_checker_page()
    elif page == "History":
        history_page()


def home_page():
    st.markdown("""
    <div class="signal-ribbon fade-in">
        <div class="signal-panel">
            <strong>Screening Command Center</strong>
            <span>Move from resume intake to shortlist decisions in one flowing workspace instead of hopping between tools.</span>
        </div>
        <div class="signal-panel">
            <strong>ATS Pulse</strong>
            <span>Catch formatting risks, section gaps, and keyword misses before candidates slip through the funnel.</span>
        </div>
        <div class="signal-panel">
            <strong>Role Fit Lens</strong>
            <span>Blend semantic match, skills coverage, and decision signals into a faster screening rhythm.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="signature-grid fade-in">
        <div class="signature-card signature-story">
            <h3>Built Like A Recruiter’s Desk, Not A Demo App</h3>
            <p>
                This workspace is designed to feel like an active screening table: resumes arrive, hiring signals sharpen, and
                the next decision becomes clearer with each pass. Instead of a plain upload-and-score flow, the app frames
                matching, ATS risk, and job discovery as one connected review rhythm.
            </p>
            <p>
                The goal is not just automation. It is a stronger point of view on how hiring teams scan, compare, and move.
            </p>
        </div>
        <div class="signature-card signature-stack">
            <h3>Signature Workflow</h3>
            <div class="stack-item">
                <span class="stack-index">01</span>
                <div class="stack-copy">
                    <strong>Ingest</strong>
                    <span>Parse resumes into structured candidate signals.</span>
                </div>
            </div>
            <div class="stack-item">
                <span class="stack-index">02</span>
                <div class="stack-copy">
                    <strong>Interpret</strong>
                    <span>Blend semantic fit, ATS health, and skill coverage.</span>
                </div>
            </div>
            <div class="stack-item">
                <span class="stack-index">03</span>
                <div class="stack-copy">
                    <strong>Act</strong>
                    <span>Shortlist faster, rank better, and search roles with context.</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown('<div class="card fade-in" style="text-align: center;"><h3 style="color: #667eea;">Resume Parsing</h3><p style="color: #64748b;">Turn raw files into structured candidate context.</p></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="card fade-in" style="text-align: center;"><h3 style="color: #667eea;">Semantic Matching</h3><p style="color: #64748b;">Compare role intent with actual candidate substance.</p></div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="card fade-in" style="text-align: center;"><h3 style="color: #667eea;">Decision Layer</h3><p style="color: #64748b;">Use sharper signals to move from review to action.</p></div>', unsafe_allow_html=True)
    
    st.markdown("### How It Works")
    steps = [("1", "Upload Resume", "PDF or DOCX"), ("2", "Add Job Description", "Paste or select skills"), ("3", "Get Analysis", "Scores & recommendations"), ("4", "Take Action", "Make hiring decisions")]
    cols = st.columns(4)
    for i, (num, title, desc) in enumerate(steps):
        with cols[i]: st.markdown(f'<div class="card" style="text-align: center; padding: 15px;"><div style="width: 40px; height: 40px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 50%; color: white; font-weight: bold; display: flex; align-items: center; justify-content: center; margin: 0 auto 10px;">{num}</div><h4 style="color: #1e293b; margin: 5px 0;">{title}</h4><p style="color: #64748b; font-size: 0.85rem;">{desc}</p></div>', unsafe_allow_html=True)
    
    if st.button("Get Started", type="primary", use_container_width=True):
        single_resume_analysis()
        return


def single_resume_analysis():
    st.markdown('<p class="sub-header">Single Resume Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown('<div class="card"><h4 style="color: #1e293b; margin-bottom: 15px;">Upload Resume</h4>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a resume file", type=['pdf', 'docx'], help="Upload PDF or DOCX", label_visibility="collapsed")
        
        if uploaded_file:
            if st.button("Parse Resume", type="primary", use_container_width=True):
                with st.spinner("Parsing resume..."):
                    try:
                        resume_data = parse_uploaded_file(uploaded_file)
                        st.session_state.resume_data = resume_data
                        st.success("Resume parsed successfully.")
                    except Exception as e: st.error(f"Error: {str(e)}")
        
        if st.session_state.resume_data:
            with st.expander("View Parsed Resume Data", expanded=False):
                st.write(f"**Name:** {st.session_state.resume_data.get('name', 'N/A')}")
                st.write(f"**Email:** {st.session_state.resume_data.get('email', 'N/A')}")
                st.write(f"**Phone:** {st.session_state.resume_data.get('phone', 'N/A')}")
                skills = st.session_state.resume_data.get('skills', [])
                if skills:
                    st.write("**Skills:**")
                    cols = st.columns(3)
                    for i, skill in enumerate(skills[:12]):
                        with cols[i % 3]: st.markdown(f'<span class="skill-tag skill-matched">{skill}</span>', unsafe_allow_html=True)
                exp = st.session_state.resume_data.get('experience', [])
                st.write(f"**Experience:** {len(exp)} entries")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card"><h4 style="color: #1e293b; margin-bottom: 15px;">Job Description</h4>', unsafe_allow_html=True)
        job_description = st.text_area("Paste job description", height=180, placeholder="Paste the job description here...", label_visibility="collapsed")
        required_skills = st.text_input("Required Skills (comma-separated)", placeholder="python, machine learning, aws, docker", help="Enter skills separated by commas")
        github_override = st.text_input("GitHub Profile (optional)", placeholder="https://github.com/username", help="Used for portfolio validation if the resume does not already include GitHub")
        
        with st.expander("Quick Skill Suggestions"):
            common_skills = ["Python", "JavaScript", "SQL", "AWS", "Docker", "React", "Machine Learning", "Data Analysis", "Git", "Agile"]
            cols = st.columns(3)
            for i, skill in enumerate(common_skills):
                with cols[i % 3]:
                    if st.button(skill, key=f"skill_{i}"):
                        required_skills = f"{required_skills}, {skill}" if required_skills else skill
        
        if st.button("Analyze Resume", type="primary", use_container_width=True, disabled=not job_description):
            if not st.session_state.resume_data:
                st.warning("Please upload and parse a resume first.")
            else:
                with st.spinner("Analyzing resume..."):
                    try:
                        if github_override:
                            st.session_state.resume_data['github'] = github_override.strip()
                        skills_list = [s.strip() for s in required_skills.split(',')] if required_skills else None
                        results = analyze_resume(st.session_state.resume_data, job_description, skills_list)
                        st.session_state.analysis_results = results
                        st.session_state.history.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'score': results['match']['overall_score'],
                            'candidate': st.session_state.resume_data.get('name', 'Unknown'),
                            'decision': results['decision']['decision']
                        })
                        st.success("Analysis complete.")
                    except Exception as e: st.error(f"Error: {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display results
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        resume_data = st.session_state.resume_data
        
        st.markdown("---")
        st.markdown("## Analysis Results")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Scores", "Skills", "Insights", "ATS", "System Checks", "Export"])
        
        with tab1:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: fig = create_gauge_chart(results['match']['overall_score'], "Overall Score"); st.plotly_chart(fig, use_container_width=True)
            with col2: fig = create_gauge_chart(results['match']['skills_score'], "Skills Score"); st.plotly_chart(fig, use_container_width=True)
            with col3: fig = create_gauge_chart(results['match']['experience_score'], "Experience Score"); st.plotly_chart(fig, use_container_width=True)
            with col4: fig = create_gauge_chart(results['ats']['score'], "ATS Score"); st.plotly_chart(fig, use_container_width=True)
            with col5: fig = create_gauge_chart(results['credibility']['overall_score'], "Trust Score"); st.plotly_chart(fig, use_container_width=True)
            
            scores = {'Overall': results['match']['overall_score'], 'Skills': results['match']['skills_score'], 'Experience': results['match']['experience_score'], 'Summary': results['match']['summary_score'], 'ATS': results['ats']['score'], 'Trust': results['credibility']['overall_score']}
            fig = create_radar_chart(scores)
            st.plotly_chart(fig, use_container_width=True)
            
            decision = results['decision']['decision']
            confidence = results['decision']['confidence']
            col1, col2 = st.columns([1, 2])
            with col1:
                if decision == 'Hire': st.markdown(f'<div style="text-align: center; padding: 20px;"><span class="decision-badge decision-hire">{decision}</span><p style="margin-top: 10px; color: #64748b;">Confidence: {confidence*100:.1f}%</p></div>', unsafe_allow_html=True)
                elif decision == 'Shortlist': st.markdown(f'<div style="text-align: center; padding: 20px;"><span class="decision-badge decision-shortlist">{decision}</span><p style="margin-top: 10px; color: #64748b;">Confidence: {confidence*100:.1f}%</p></div>', unsafe_allow_html=True)
                else: st.markdown(f'<div style="text-align: center; padding: 20px;"><span class="decision-badge decision-reject">{decision}</span><p style="margin-top: 10px; color: #64748b;">Confidence: {confidence*100:.1f}%</p></div>', unsafe_allow_html=True)
            with col2:
                st.write("**Reasons:**")
                for reason in results['decision']['reasons']: st.write(f"- {reason}")
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                fig = create_skill_pie_chart(results['match']['matched_skills'], results['match']['missing_skills'])
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.write("**Matched Skills:**")
                if results['match']['matched_skills']:
                    for skill in results['match']['matched_skills']: st.markdown(f'<span class="skill-tag skill-matched">{skill}</span>', unsafe_allow_html=True)
                else: st.info("No matches found")
                st.write("")
                st.write("**Missing Skills:**")
                if results['match']['missing_skills']:
                    for skill in results['match']['missing_skills']: st.markdown(f'<span class="skill-tag skill-missing">{skill}</span>', unsafe_allow_html=True)
                else: st.success("No missing skills!")
            
            st.write("**Skill Categories:**")
            categories = results['skills']['categories']
            for cat, data in categories.items():
                if data['skills']:
                    with st.expander(f"{cat.title()} ({len(data['skills'])} skills)"):
                        for skill in data['skills']: st.write(f"- {skill}")
        
        with tab3:
            additional = results['additional']
            
            st.markdown('<div class="card"><h4 style="color: #1e293b;">Estimated Salary Range</h4>', unsafe_allow_html=True)
            salary = additional['estimated_salary']
            st.markdown(f'<p style="font-size: 1.8rem; font-weight: 700; color: #10b981; text-align: center;">${salary["min"]:,} - ${salary["max"]:,} {salary["currency"]}</p><p style="text-align: center; color: #64748b;">Based on skills and experience</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("### Suggested Interview Questions")
            questions = additional['interview_questions']
            for i, q in enumerate(questions):
                with st.expander(f"Q{i+1}: {q['question']}"): st.write(f"**Category:** {q['category']}")
            
            if additional['learning_resources']:
                st.markdown("### Learning Resources for Missing Skills")
                for skill, resources in additional['learning_resources'].items():
                    with st.expander(f"Learn {skill}"):
                        st.write("**Courses:**")
                        for course in resources.get('courses', []): st.write(f"- {course}")
                        st.write("**YouTube:**")
                        for yt in resources.get('youtube', []): st.write(f"- {yt}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="card"><h4 style="color: #10b981;">Strengths</h4>', unsafe_allow_html=True)
                if additional['strengths']:
                    for s in additional['strengths']: st.write(f"- {s}")
                else: st.info("No specific strengths identified")
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="card"><h4 style="color: #ef4444;">Areas for Improvement</h4>', unsafe_allow_html=True)
                if additional['weaknesses']:
                    for w in additional['weaknesses']: st.write(f"- {w}")
                else: st.success("No major weaknesses identified")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("### Recommendations")
            for rec in results['decision']['recommendations']: st.write(f"- {rec}")
        
        with tab4:
            st.markdown("### ATS Compatibility")
            fig = create_gauge_chart(results['ats']['score'], "ATS Score")
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("**Section Analysis:**")
            sections = results['ats']['section_analysis']
            for section, found in sections.items():
                if found: st.success(f"{section.title()} section found")
                else: st.error(f"{section.title()} section missing")
            
            if results['ats']['issues']:
                st.write("**Issues Found:**")
                for issue in results['ats']['issues']:
                    severity = issue.get('severity', 'low')
                    if severity == 'high': st.error(issue['message'])
                    elif severity == 'medium': st.warning(issue['message'])
                    else: st.info(issue['message'])
            
            if results['ats']['suggestions']:
                st.write("**Suggestions:**")
                for suggestion in results['ats']['suggestions']: st.write(f"- {suggestion}")

        with tab5:
            trust = results['credibility']
            st.markdown("### Candidate Credibility Checks")

            col1, col2 = st.columns([1, 1.4])
            with col1:
                fig = create_gauge_chart(trust['overall_score'], "System Trust Score")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("""
                <div class="glass-note">
                    <strong>Checks run</strong><br/>
                    Fake skills based on project evidence<br/>
                    GitHub validation against public profile signals<br/>
                    Experience consistency across timeline claims
                </div>
                """, unsafe_allow_html=True)
            with col2:
                github_username = trust.get('github_profile', {}).get('username')
                st.write(f"**GitHub Source:** {github_username or resume_data.get('github', 'Not provided') or 'Not provided'}")
                if trust['flags']:
                    st.write("**Review Flags:**")
                    for flag in trust['flags']:
                        st.warning(flag)
                else:
                    st.success("No major credibility flags were raised.")

            for key in ['fake_skills', 'github_validation', 'experience_consistency']:
                signal = trust[key]
                with st.expander(f"{signal['name']} - {signal['score']:.1f}/100"):
                    st.write(signal['summary'])
                    for item in signal['evidence']:
                        st.write(f"- {item}")

        with tab6:
            st.write("**Export Analysis Results**")
            csv = export_to_csv(results, resume_data)
            st.download_button(label="Download CSV", data=csv, file_name=f"resume_analysis_{resume_data.get('name', 'candidate')}.csv", mime="text/csv", use_container_width=True)
            
            json_data = json.dumps(results, indent=2)
            st.download_button(label="Download JSON", data=json_data, file_name=f"resume_analysis_{resume_data.get('name', 'candidate')}.json", mime="application/json", use_container_width=True)
            
            st.write("**Resume Classification:**")
            st.write(f"**Category:** {results['classification']['category']}")
            st.write(f"**Confidence:** {results['classification']['confidence']*100:.1f}%")


def batch_ranking():
    st.markdown('<p class="sub-header">Batch Resume Ranking</p>', unsafe_allow_html=True)
    st.write("Upload multiple resumes to rank candidates for a job position.")
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        job_description = st.text_area("Job Description", height=150, placeholder="Paste job description...", label_visibility="collapsed")
        required_skills = st.text_input("Required Skills (comma-separated)", placeholder="python, sql, aws", help="Enter skills separated by commas")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Upload Resumes (multiple)", type=['pdf', 'docx'], accept_multiple_files=True, help="Upload multiple PDF or DOCX files", label_visibility="collapsed")
        if uploaded_files: st.success(f"{len(uploaded_files)} files uploaded")
        st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("Rank Candidates", type="primary", use_container_width=True):
        if not uploaded_files: st.warning("Please upload resumes first.")
        elif not job_description: st.warning("Please provide a job description.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            skills_list = [s.strip() for s in required_skills.split(',')] if required_skills else None
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))
                try:
                    resume_data = parse_uploaded_file(uploaded_file)
                    analysis = analyze_resume(resume_data, job_description, skills_list)
                    results.append({'resume_data': resume_data, 'results': analysis, 'score': analysis['match']['overall_score']})
                except Exception as e: st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            results.sort(key=lambda x: x['score'], reverse=True)
            st.session_state.batch_results = results
            status_text.text("Analysis complete.")
            progress_bar.empty()
            st.success(f"Analyzed {len(results)} resumes.")
    
    if st.session_state.batch_results:
        st.markdown("---")
        st.markdown("## Candidate Rankings")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_score = sum(r['score'] for r in st.session_state.batch_results) / len(st.session_state.batch_results)
            st.metric("Average Score", f"{avg_score:.1f}%")
        with col2:
            top_score = max(r['score'] for r in st.session_state.batch_results)
            st.metric("Highest Score", f"{top_score:.1f}%")
        with col3: st.metric("Total Candidates", len(st.session_state.batch_results))
        
        for i, item in enumerate(st.session_state.batch_results):
            display_candidate_card(item['results'], item['resume_data'], rank=i+1)
            with st.expander(f"View Details for #{i+1} - {item['resume_data'].get('name', 'Unknown')}"):
                results = item['results']
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Match Scores:**")
                    st.write(f"- Overall: {results['match']['overall_score']:.1f}%")
                    st.write(f"- Skills: {results['match']['skills_score']:.1f}%")
                    st.write(f"- Experience: {results['match']['experience_score']:.1f}%")
                    st.write(f"- ATS: {results['ats']['score']:.1f}%")
                with col2:
                    st.write("**Matched Skills:**")
                    for skill in results['match']['matched_skills'][:5]: st.markdown(f'<span class="skill-tag skill-matched">{skill}</span>', unsafe_allow_html=True)
                    st.write("")
                    st.write("**Missing Skills:**")
                    for skill in results['match']['missing_skills'][:5]: st.markdown(f'<span class="skill-tag skill-missing">{skill}</span>', unsafe_allow_html=True)
        
        if st.button("Export All Results", type="secondary"):
            data = []
            for item in st.session_state.batch_results:
                data.append({
                    'Rank': st.session_state.batch_results.index(item) + 1,
                    'Name': item['resume_data'].get('name', 'N/A'),
                    'Email': item['resume_data'].get('email', 'N/A'),
                    'Score': item['score'],
                    'Decision': item['results']['decision']['decision'],
                    'Matched Skills': ', '.join(item['results']['match']['matched_skills']),
                    'Missing Skills': ', '.join(item['results']['match']['missing_skills'])
                })
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            st.download_button(label="Download CSV", data=csv, file_name="candidate_rankings.csv", mime="text/csv", use_container_width=True)


def job_search():
    st.markdown('<p class="sub-header">Job Search</p>', unsafe_allow_html=True)
    st.info("Search jobs with a guided flow: choose country, state, district, then run your keyword search.")

    geography = {
        "global": {"All": ["All", "Remote", "Worldwide", "EMEA", "APAC"]},
        "in": {
            "Delhi NCR": ["All", "New Delhi", "Gurugram", "Noida", "Faridabad", "Ghaziabad"],
            "Karnataka": ["All", "Bengaluru Urban", "Mysuru", "Mangaluru", "Hubballi"],
            "Maharashtra": ["All", "Mumbai", "Pune", "Nagpur", "Navi Mumbai", "Thane"],
            "Tamil Nadu": ["All", "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli"],
            "Telangana": ["All", "Hyderabad", "Warangal", "Nizamabad", "Karimnagar"],
            "West Bengal": ["All", "Kolkata", "Howrah", "Siliguri", "Durgapur"],
            "Gujarat": ["All", "Ahmedabad", "Surat", "Vadodara", "Rajkot"],
            "Kerala": ["All", "Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur"],
        },
        "us": {
            "California": ["All", "San Francisco", "San Jose", "Oakland", "Los Angeles", "San Diego", "Irvine"],
            "Texas": ["All", "Austin", "Dallas", "Houston", "San Antonio", "Plano"],
            "New York": ["All", "New York City", "Brooklyn", "Queens", "Buffalo", "Albany"],
            "Washington": ["All", "Seattle", "Bellevue", "Redmond", "Tacoma", "Spokane"],
            "Illinois": ["All", "Chicago", "Naperville", "Schaumburg"],
            "Massachusetts": ["All", "Boston", "Cambridge", "Somerville"],
        },
        "uk": {
            "England": ["All", "London", "Manchester", "Birmingham", "Leeds", "Bristol"],
            "Scotland": ["All", "Edinburgh", "Glasgow", "Aberdeen"],
            "Wales": ["All", "Cardiff", "Swansea", "Newport"],
        },
        "ca": {
            "Ontario": ["All", "Toronto", "Ottawa", "Mississauga", "Brampton", "Waterloo"],
            "British Columbia": ["All", "Vancouver", "Victoria", "Surrey", "Burnaby"],
            "Quebec": ["All", "Montreal", "Quebec City", "Laval"],
            "Alberta": ["All", "Calgary", "Edmonton", "Red Deer"],
        },
        "au": {
            "New South Wales": ["All", "Sydney", "Newcastle", "Wollongong"],
            "Victoria": ["All", "Melbourne", "Geelong", "Ballarat"],
            "Queensland": ["All", "Brisbane", "Gold Coast", "Sunshine Coast"],
            "Western Australia": ["All", "Perth", "Fremantle", "Mandurah"],
        },
    }

    col1, col2, col3, col4, col5 = st.columns([1.2, 1, 1, 1, 1.1])
    with col1:
        location = st.selectbox("Country", ["global", "in", "us", "uk", "ca", "au"], index=0)
    states = list(geography.get(location, {"All": ["All"]}).keys())
    with col2:
        state = st.selectbox("State", states, index=0)
    districts = geography.get(location, {}).get(state, ["All"])
    with col3:
        district = st.selectbox("District", districts, index=0)
    with col4:
        category = st.selectbox("Category", ["", "software", "marketing", "design", "sales", "business", "data", "devops"])
    with col5:
        keyword = st.text_input("Search", placeholder="python developer")
    
    # Job sources selector
    st.markdown("<div class='card' style='padding: 15px; margin-top: 15px;'><strong>Search From:</strong></div>", unsafe_allow_html=True)
    sources_col1, sources_col2, sources_col3, sources_col4 = st.columns(4)
    with sources_col1:
        use_remotive = st.checkbox("🌐 Remotive", value=True, help="Remote jobs from Remotive")
    with sources_col2:
        use_unstop = st.checkbox("🇮🇳 Unstop", value=True, help="Jobs & internships from Unstop (India)")
    with sources_col3:
        use_internshala = st.checkbox("📚 Internshala", value=True, help="Internships from Internshala")
    with sources_col4:
        use_glassdoor = st.checkbox("💼 Glassdoor", value=True, help="Jobs from Glassdoor")
    
    # Build sources list
    selected_sources = []
    if use_remotive:
        selected_sources.append("remotive")
    if use_unstop:
        selected_sources.append("unstop")
    if use_internshala:
        selected_sources.append("internshala")
    if use_glassdoor:
        selected_sources.append("glassdoor")
    
    if st.button("Search Jobs", type="primary", use_container_width=True):
        if not selected_sources:
            st.error("Please select at least one job source!")
        else:
            with st.spinner("Searching for jobs from selected sources..."):
                try:
                    fetcher = JobDataFetcher()
                    jobs = fetcher.fetch_jobs_by_keyword(
                        keyword=keyword or "developer",
                        location=location,
                        sources=selected_sources,
                        category=category or None,
                        state=None if state == "All" else state,
                        district=None if district == "All" else district
                    )
                    st.session_state.search_results = jobs
                    st.success(f"Found {len(jobs)} jobs from {', '.join(selected_sources)}!")
                except Exception as e: st.error(f"Error: {str(e)}")
    
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.markdown("---")
        st.metric("Jobs Found", len(st.session_state.search_results))
        st.caption("Results are filtered by country, state, district, category, and keyword relevance when those details are present in the listing.")
        pulse = build_market_pulse(st.session_state.search_results)
        st.markdown(f"""
        <div class="pulse-grid fade-in">
            <div class="pulse-card">
                <strong>Metro Match Pulse</strong>
                <span>Most active metro cluster in current results: {pulse["top_metro"]}</span>
            </div>
            <div class="pulse-card">
                <strong>Remote Readiness</strong>
                <span>{pulse["remote_share"]} of the current roles explicitly mention remote support.</span>
            </div>
            <div class="pulse-card">
                <strong>Skill Signal</strong>
                <span>The strongest recurring skill in this search is <b>{pulse["top_skill"]}</b>.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for job in st.session_state.search_results:
            with st.container():
                st.markdown(f"""
                <div class="card fade-in">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h3 style="color: #1e293b; margin: 0;">{job.title}</h3>
                            <p style="color: #64748b; margin: 5px 0;">{job.company} | {job.location}</p>
                            <p style="color: #64748b; margin: 5px 0;">{job.job_type}</p>
                        </div>
                """, unsafe_allow_html=True)
                st.markdown(f"[Apply Now]({job.url})", unsafe_allow_html=True)
                st.markdown("</div></div>", unsafe_allow_html=True)
                
                with st.expander("View Description"):
                    st.write(job.description[:1500] + "..." if len(job.description) > 1500 else job.description)
                
                if job.skills:
                    st.write("**Skills:**")
                    cols = st.columns(4)
                    for i, skill in enumerate(job.skills[:8]):
                        with cols[i % 4]: st.markdown(f'<span class="skill-tag skill-matched">{skill}</span>', unsafe_allow_html=True)
                
                st.divider()
    elif 'search_results' in st.session_state:
        st.markdown("---")
        st.warning("No jobs matched the selected country, state, and district. Try a nearby metropolitan district or broaden the search.")


def ats_checker_page():
    st.markdown('<p class="sub-header">ATS Compatibility Checker</p>', unsafe_allow_html=True)
    st.write("Check if your resume is ATS-friendly and get improvement suggestions.")
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload Resume", type=['pdf', 'docx'], label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        job_description = st.text_area("Job Description (optional)", height=150, placeholder="Paste job description for keyword analysis...", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_file and st.button("Check ATS", type="primary", use_container_width=True):
        with st.spinner("Checking ATS compatibility..."):
            try:
                resume_data = parse_uploaded_file(uploaded_file)
                ats_checker = ATSChecker()
                result = ats_checker.check_resume(resume_data, job_description)
                st.session_state.ats_results = result
                st.success("ATS check complete.")
            except Exception as e: st.error(f"Error: {str(e)}")
    
    if 'ats_results' in st.session_state and st.session_state.ats_results:
        result = st.session_state.ats_results
        st.markdown("---")
        
        fig = create_gauge_chart(result.score, "ATS Score")
        st.plotly_chart(fig, use_container_width=True)
        
        tab1, tab2, tab3 = st.tabs(["Sections", "Issues", "Suggestions"])
        
        with tab1:
            st.write("**Section Analysis:**")
            sections = result.section_analysis
            for section, found in sections.items():
                if found: st.success(f"{section.title()} section found")
                else: st.error(f"{section.title()} section missing")
        
        with tab2:
            if result.issues:
                for issue in result.issues:
                    severity = issue.get('severity', 'low')
                    if severity == 'high': st.error(f"**{severity.upper()}** - {issue['message']}")
                    elif severity == 'medium': st.warning(f"**{severity.upper()}** - {issue['message']}")
                    else: st.info(f"**{severity.upper()}** - {issue['message']}")
            else: st.success("No issues found! Your resume looks ATS-friendly.")
        
        with tab3:
            if result.suggestions:
                for i, suggestion in enumerate(result.suggestions, 1): st.write(f"{i}. {suggestion}")
            else: st.info("No specific suggestions. Your resume looks good!")


def history_page():
    st.markdown('<p class="sub-header">Analysis History</p>', unsafe_allow_html=True)
    
    if not st.session_state.history:
        st.info("No analysis history yet. Start analyzing resumes to see history here.")
        if st.button("Go to Analysis"):
            single_resume_analysis()
            return
    else:
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total Analyses", len(st.session_state.history))
        with col2:
            avg_score = sum(h['score'] for h in st.session_state.history) / len(st.session_state.history)
            st.metric("Average Score", f"{avg_score:.1f}%")
        with col3:
            hire_count = sum(1 for h in st.session_state.history if h['decision'] == 'Hire')
            st.metric("Hire Decisions", hire_count)
        
        fig = create_score_history_chart(st.session_state.history)
        if fig: st.plotly_chart(fig, use_container_width=True)
        
        st.write("**Recent Analyses:**")
        history_data = []
        for h in reversed(st.session_state.history[-10:]):
            history_data.append({"Time": h['timestamp'], "Candidate": h['candidate'], "Score": f"{h['score']:.1f}%", "Decision": h['decision']})
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        if st.button("Clear History", type="secondary"):
            st.session_state.history = []
            st.success("History cleared!")
            st.rerun()


if __name__ == "__main__":
    main()

