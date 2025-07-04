# FairScan
An Ontology-Driven Resume Screening Framework for Bias-Free, Context-Autonomous Recruitment

## 🚀 Overview
Fairscan revolutionizes AI-powered resume screening by eliminating external biases and ensuring complete organizational context autonomy. Unlike traditional systems that rely on generic pre-trained models, Fairscan leverages semantic reasoning and organization-specific ontologies to provide transparent, interpretable, and contextually relevant candidate evaluations.

### ✨ Key Features

##### 1. 🎯 Bias-Free Screening: Eliminates external biases from pre-trained models
##### 2. 🏢 Organizational Autonomy: Operates entirely within your infrastructure
##### 3. 🧠 Cache Augmented Generation: Novel CAG methodology for efficient semantic processing
##### 4. 📊 SBERT Integration: Advanced semantic similarity matching
##### 5. ⚡ KV Cache Optimization: Fast ontology-driven context retrieval
##### 6. 🔒 Privacy-First: Complete data sovereignty with no external dependencies
##### 7. 📊 Transparent Decisions: Interpretable screening results with clear reasoning
##### 8. ⚙️ Customizable Ontologies: HR-defined contexts for job requirements and cultural values

### 🎯 Problem Solved
Traditional AI resume screening systems face three critical challenges:

1. Bias Propagation: Inherit irrelevant biases from external training datasets
2. Privacy Vulnerabilities: Risk exposure of sensitive candidate information
3. Context Misalignment: Fail to capture organization-specific requirements and values

Fairscan addresses these issues through semantic knowledge representation that accurately captures and utilizes organization-specific hiring contexts.

## 🏗️ Architecture![main](https://github.com/user-attachments/assets/e272e909-738d-45ce-a4ca-a297a72a5fb5)


Fairscan implements a novel Cache Augmented Generation (CAG) methodology that combines semantic reasoning with efficient knowledge retrieval:

### Core Components:

#### 1.📥 HR Input Layer

PDF/DOCX resume processing
Ontology document management


#### 2.🔄 Document Processing Engine

Text extraction with privacy obfuscation
Personal data anonymization


#### 3.🧠 Ontology Processing

KV Cache generation for semantic efficiency
Context window preloading
Job description extraction and structuring


#### 4.🎯 Job Description Matching

SBERT-based semantic similarity scoring
Best job classification and ranking
Multi-criteria evaluation framework


#### 5.⚡ Cache Augmented Generation (CAG)

Resume text + matched job description fusion
Ontology KV Cache integration for contextual reasoning
Semantic analysis optimization


#### 6.🤖 Open Source LLM Integration

Privacy-preserving local inference
Semantic analysis and intelligent scoring
Bias-free evaluation pipeline


#### 7.📊 Results & Review System

Criteria-based scoring with transparency
Detailed reasoning and recommendations
HR review integration with audit trails

# Project Requirements

## System Requirements
- **GPU Memory**: 6GB VRAM minimum
- **CUDA**: Enabled environment required
- **MySql Workbench 8.0**

## Software Requirements
- **Python**: 3.10
- **llama-cpp-python**: Latest version
- **PyTorch**: Latest with CUDA 12.4 support
- **Torchvision**: Latest with CUDA 12.4 support

## Installation Steps

### 1. Set Environment Variables (Windows PowerShell)
```powershell
$Env:LLAMA_CUBLAS = "1"
$Env:FORCE_CMAKE = "1"
$Env:CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_GENERATOR_TOOLSET=cuda='C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1'"
```

### 2. Install llama-cpp-python
```
pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
```

### 3. Install PyTorch with CUDA Support
```
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### 4. Install the requirements.txt 
```
pip install -r ./requirements.txt
```

##### Note




🚀 Quick Start
1. Define Your Organizational Ontology
