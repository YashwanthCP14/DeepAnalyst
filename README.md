# DeepAnalyst
An autonomous Data Analyst Using Gemini & Ollama

DeepAnalyst is an AI-assisted data analysis platform for exploring, understanding, and modeling structured datasets.

The project combines automated data profiling, statistical analysis, machine learning, and large language model reasoning into a single workflow. It is designed to reduce the manual effort required to inspect datasets, generate visualizations, build predictive models, and interpret analytical results.

---

## Motivation

Modern data analysis typically involves multiple disconnected tools for preprocessing, visualization, modeling, and reporting. This fragmentation increases development time and makes iterative analysis difficult.

DeepAnalyst provides a unified interface that automates common analytical workflows while keeping the underlying process transparent and reproducible.

---

## Capabilities

* Automated exploratory data analysis
* Dataset profiling
* Data quality assessment
* Missing value analysis
* Statistical summaries
* Interactive visualizations
* Feature engineering
* Machine learning pipelines
* Model evaluation
* AI-assisted interpretation
* Automated report generation

---

## Architecture

```text
Dataset
    │
    ▼
Validation
    │
    ▼
Preprocessing
    │
    ▼
Exploratory Data Analysis
    │
    ▼
Feature Engineering
    │
    ▼
Machine Learning
    │
    ▼
Large Language Model
    │
    ▼
Reports and Visualizations
```

---

## Technology Stack

### Core

* Python
* Streamlit

### Data Processing

* Pandas
* NumPy

### Machine Learning

* Scikit-learn
* XGBoost

### Visualization

* Plotly
* Matplotlib
* Seaborn

### AI

* Google Gemini
* Ollama (optional)

---

## Installation

Clone the repository.

```bash
git clone https://github.com/YashwanthCP14/DeepAnalyst.git
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate the environment.

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Start the application.

```bash
streamlit run app.py
```

---

## Repository Structure

```text
DeepAnalyst/
├── app.py
├── requirements.txt
├── data/
├── models/
├── notebooks/
├── reports/
├── assets/
└── utils/
```

---

## Workflow

1. Load a structured dataset.
2. Validate the input.
3. Profile and preprocess the data.
4. Explore statistical summaries and visualizations.
5. Train predictive models.
6. Evaluate model performance.
7. Generate AI-assisted analytical summaries.
8. Export results.

---

## Supported Workloads

DeepAnalyst currently focuses on structured tabular datasets and supports workflows including:

* Classification
* Regression
* Customer analytics
* Employee attrition analysis
* Sales forecasting
* Business intelligence
* General exploratory data analysis

---

## Design Principles

The project is built around a small set of principles:

* Automation without sacrificing transparency
* Reproducible analytical workflows
* Human-readable outputs
* Modular architecture
* Extensible components
* Practical developer experience

---

## Roadmap

Planned improvements include:

* Database connectors
* Time-series forecasting
* Explainable AI
* Retrieval-Augmented Generation
* REST API
* Docker support
* Authentication
* Cloud deployment
* Multi-user workspaces

---

## Contributing

Contributions are welcome.

Bug reports, feature requests, and pull requests are encouraged. Please open an issue before submitting significant architectural changes.

---

## License

This project is released under the MIT License.
