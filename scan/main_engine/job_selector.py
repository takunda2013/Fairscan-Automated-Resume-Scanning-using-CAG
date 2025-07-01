
import os
import json
import numpy as np
import fitz  # PyMuPDF
from pathlib import Path
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import Dict, List, Optional, Tuple
import re
from collections import Counter

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

class WeightedJobSelector:
    def __init__(self, use_offline: bool = True, offline_models_dir: str = r"C:\Fairscan\takundajori\mysite\scan\main_engine\models"):
        self.offline_models_dir = Path(offline_models_dir)
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None
        self.use_tfidf = False
        self.vectorizer = None
        self.jobs_db = []
        self.job_embeddings = None
        self.faiss_index = None
        
        # New weighted matching components
        self.job_skill_weights = []
        self.job_requirement_texts = []
        
        if use_offline:
            self._load_offline_model()
        else:
            self._load_online_model()
    
    def _load_online_model(self):
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"✓ Loaded online model: {self.model_name}")
        except Exception as e:
            print(f"Failed to load online model: {e}")
            self._load_offline_model()
    
    def _load_offline_model(self):
        local_model_path = self.offline_models_dir / self.model_name
        if local_model_path.exists():
            try:
                self.model = SentenceTransformer(str(local_model_path))
                print(f"✓ Loaded offline model: {local_model_path}")
            except Exception as e:
                print(f"Failed to load offline model: {e}")
                self._setup_tfidf()
        else:
            print(f"Offline model not found: {local_model_path}")
            self._setup_tfidf()
    
    def _setup_tfidf(self):
        self.model = None
        self.use_tfidf = True
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        print("✓ Using TF-IDF embeddings")
    
    def extract_resume_text(self, resume_path: str) -> str:
        """Extract text from PDF using PyMuPDF (fitz)"""
        try:
            doc = fitz.open(resume_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text.strip()
        except Exception as e:
            print(f"Error reading resume {resume_path}: {e}")
            return ""
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract individual skills from comma-separated text"""
        if not text:
            return []
        
        # Split by comma and clean up
        skills = [skill.strip().lower() for skill in text.split(',')]
        # Remove empty strings
        skills = [skill for skill in skills if skill]
        return skills
    
    def _calculate_skill_weights(self, job_data: Dict) -> Dict[str, float]:
        """
        Calculate skill weights based on job requirements structure.
        This is generic and works for any job format.
        """
        weights = {}
        
        # Extract skills from the skills field
        skills_text = job_data.get('skills', '')
        skills_list = self._extract_skills_from_text(skills_text)
        
        # Extract requirements structure if available
        requirements = job_data.get('requirements', '')
        requirement_categories = [req.strip() for req in requirements.split(',')]
        
        # Base weight for all skills
        base_weight = 1.0
        
        # If we have requirement categories, we can infer importance
        num_categories = len(requirement_categories) if requirement_categories else 1
        skills_per_category = len(skills_list) // num_categories if num_categories > 0 else len(skills_list)
        
        # Assign weights: earlier categories get higher weights (assuming they're listed by importance)
        for i, skill in enumerate(skills_list):
            category_index = i // skills_per_category if skills_per_category > 0 else 0
            category_index = min(category_index, num_categories - 1)
            
            # Weight decreases for later categories: 1.0, 0.8, 0.6, 0.4, 0.2
            weight = max(0.2, 1.0 - (category_index * 0.2))
            weights[skill] = weight
        
        return weights
    
    def _generate_skill_patterns(self, all_job_skills: List[str]) -> Dict[str, List[str]]:
        """Dynamically generate skill patterns from job requirements"""
        skill_patterns = {}
        
        for skill in all_job_skills:
            skill_lower = skill.lower().strip()
            if not skill_lower:
                continue
                
            # Create pattern variations for each skill
            patterns = [skill_lower]
            
            # Add common variations
            if '.' in skill_lower:
                patterns.append(skill_lower.replace('.', ''))
            if ' ' in skill_lower:
                patterns.append(skill_lower.replace(' ', ''))
                patterns.append(skill_lower.replace(' ', '-'))
            
            # Add acronyms for multi-word skills
            if ' ' in skill_lower:
                words = skill_lower.split()
                if len(words) > 1:
                    acronym = ''.join(word[0] for word in words if word)
                    if len(acronym) > 1:
                        patterns.append(acronym)
            
            # Add common tech variations
            if skill_lower.endswith('js'):
                base = skill_lower[:-2]
                patterns.extend([base, f"{base}.js"])
            elif 'javascript' in skill_lower:
                patterns.extend(['js', 'ecmascript'])
            elif skill_lower == 'css':
                patterns.extend(['css3', 'cascading style sheets'])
            elif skill_lower == 'html':
                patterns.extend(['html5', 'hypertext markup'])
            
            skill_patterns[skill_lower] = list(set(patterns))
        
        return skill_patterns

    def _calculate_resume_skill_frequency(self, resume_text: str, job_skills: List[str]) -> Dict[str, int]:
        """Calculate frequency of job-specific skills mentioned in resume"""
        resume_lower = resume_text.lower()
        skill_frequency = {}
        
        # Generate patterns dynamically from job skills
        skill_patterns = self._generate_skill_patterns(job_skills)
        
        # Count occurrences using word boundaries for better matching
        for skill, patterns in skill_patterns.items():
            total_frequency = 0
            for pattern in patterns:
                # Use word boundaries for exact matching
                matches = len(re.findall(r'\b' + re.escape(pattern) + r'\b', resume_lower))
                total_frequency += matches
            
            if total_frequency > 0:
                skill_frequency[skill] = total_frequency
        
        return skill_frequency
    
    def _calculate_weighted_similarity(self, job_idx: int, resume_text: str, base_similarity: float) -> float:
        """
        Calculate weighted similarity based on skill importance and resume skill depth
        """
        job_data = self.jobs_db[job_idx]
        skill_weights = self.job_skill_weights[job_idx]
        
        # Get job skills for this specific job
        job_skills = self._extract_skills_from_text(job_data.get('skills', ''))
        resume_skill_freq = self._calculate_resume_skill_frequency(resume_text, job_skills)
        
        if not skill_weights or not resume_skill_freq:
            return base_similarity
        
        # Calculate weighted skill match score
        total_weighted_score = 0.0
        total_possible_weight = 0.0
        matched_skills = []
        
        for skill, weight in skill_weights.items():
            total_possible_weight += weight
            
            # Check if skill exists in resume frequency analysis
            skill_score = resume_skill_freq.get(skill, 0)
            if skill_score > 0:
                # Score based on frequency: log scale to avoid over-weighting
                normalized_score = min(1.0, np.log(skill_score + 1) / np.log(10))
                matched_skills.append((skill, skill_score, weight))
                total_weighted_score += normalized_score * weight
        
        # Normalize weighted score
        weighted_skill_ratio = total_weighted_score / total_possible_weight if total_possible_weight > 0 else 0.0
        
        # Combine base semantic similarity with weighted skill matching
        # 60% semantic similarity + 40% weighted skill matching
        final_score = (0.6 * base_similarity) + (0.4 * weighted_skill_ratio)
        
        # Debug information
        if matched_skills:
            print(f"   Matched skills for {job_data['title']}:")
            for skill, freq, weight in matched_skills[:5]:  # Top 5
                print(f"     - {skill} (freq: {freq}, weight: {weight:.2f})")
        
        return final_score
    
    def prepare_job_database(self, jobs_data: List[Dict]):
        print(f"Processing {len(jobs_data)} job descriptions...")
        self.jobs_db = jobs_data
        self.job_skill_weights = []
        self.job_requirement_texts = []
        
        job_texts = []
        for job in jobs_data:
            # Combine all job information for semantic matching
            combined_text = f"Title: {job.get('title', '')}\n"
            combined_text += f"Description: {job.get('description', '')}\n"
            combined_text += f"Requirements: {job.get('requirements', '')}\n"
            combined_text += f"Skills: {job.get('skills', '')}"
            job_texts.append(combined_text.strip())
            
            # Calculate skill weights for this job
            skill_weights = self._calculate_skill_weights(job)
            self.job_skill_weights.append(skill_weights)
            
            # Store requirement text for debugging
            self.job_requirement_texts.append(job.get('requirements', ''))
        
        if self.use_tfidf:
            self.job_embeddings = self.vectorizer.fit_transform(job_texts)
        else:
            self.job_embeddings = self.model.encode(job_texts, 
                                                show_progress_bar=True,
                                                convert_to_numpy=True)
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(self.job_embeddings)
        
        dimension = self.job_embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        
        # Add to FAISS index
        if self.use_tfidf:
            # Convert sparse to dense for FAISS
            dense_embeddings = self.job_embeddings.toarray()
            norms = np.linalg.norm(dense_embeddings, axis=1, keepdims=True)
            dense_embeddings = dense_embeddings / (norms + 1e-8)
            self.faiss_index.add(dense_embeddings.astype('float32'))
        else:
            self.faiss_index.add(self.job_embeddings.astype('float32'))
        
        print(f"✓ Job database ready with {len(jobs_data)} positions")
        print(f"✓ Skill weights calculated for weighted matching")
    
    def find_top_match(self, resume_input: str) -> Tuple[Optional[Dict], float]:
        """Find best matching job using weighted semantic similarity"""
        if not self.faiss_index:
            return None, 0.0

        # Handle both file path and direct text input
        if isinstance(resume_input, str) and resume_input.endswith('.pdf'):
            resume_text = self.extract_resume_text(resume_input)
        else:
            resume_text = resume_input

        if not resume_text:
            return None, 0.0

        # Generate resume embedding - Prioritize sentence-transformers
        if self.model and not self.use_tfidf:
            print(f"📋 Using sentence-transformers for weighted semantic search...")
            resume_embedding = self.model.encode([resume_text])
            if len(resume_embedding) == 0:
                return None, 0.0
            faiss.normalize_L2(resume_embedding)
        else:
            print(f"📋 Fallback: Using TF-IDF for weighted semantic search...")
            resume_embedding = self.vectorizer.transform([resume_text])
            if resume_embedding.nnz == 0:
                return None, 0.0
            resume_embedding = resume_embedding.toarray()
            norm = np.linalg.norm(resume_embedding)
            resume_embedding = resume_embedding / (norm + 1e-8)

        # Check dimension compatibility
        if resume_embedding.shape[1] != self.faiss_index.d:
            return None, 0.0

        # Get base semantic similarities
        top_k = min(10, len(self.jobs_db))
        similarities, indices = self.faiss_index.search(
            resume_embedding.astype('float32'), top_k
        )

        print("🔍 Base Semantic Matches:")
        weighted_results = []
        
        for i, (base_similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            job_title = self.jobs_db[idx].get("title", "Unknown Title")
            print(f"{i+1}. {job_title} | Base Similarity: {base_similarity:.3f}")
            
            # Calculate weighted similarity
            weighted_similarity = self._calculate_weighted_similarity(
                idx, resume_text, float(base_similarity)
            )
            
            weighted_results.append((idx, weighted_similarity, base_similarity))
            print(f"   → Weighted Score: {weighted_similarity:.3f}")

        # Sort by weighted similarity
        weighted_results.sort(key=lambda x: x[1], reverse=True)
        
        print("\n🏆 Final Weighted Rankings:")
        for i, (idx, weighted_sim, base_sim) in enumerate(weighted_results[:5]):
            job_title = self.jobs_db[idx].get("title", "Unknown Title")
            print(f"{i+1}. {job_title} | Weighted: {weighted_sim:.3f} | Base: {base_sim:.3f}")

        # Return best weighted match
        if weighted_results and weighted_results[0][1] > 0:
            best_job_idx, best_weighted_score, best_base_score = weighted_results[0]
            print(f"\n🎯 Best Weighted Match: {self.jobs_db[best_job_idx].get('title', 'Unknown')} | Score: {best_weighted_score:.3f}")
            return self.jobs_db[best_job_idx], best_weighted_score
        
        return None, 0.0

# Backward compatibility
JobSelector = WeightedJobSelector