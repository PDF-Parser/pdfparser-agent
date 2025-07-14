from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pdfparser-agent",
    version="0.1.0",
    author="Priyesh Srivastava",
    author_email="priyesh@example.com",  # Update with actual email
    description="A next-generation PDF reader fully orchestrated by AI Agents",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/priyeshsrivastava/pdfparser-agent",  # Update with actual repo URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pdfparser-agent=pdfparser_agent.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pdfparser_agent": ["*.md", "*.txt"],
    },
    keywords="pdf, ai, agent, parser, document, langgraph",
    project_urls={
        "Bug Reports": "https://github.com/priyeshsrivastava/pdfparser-agent/issues",
        "Source": "https://github.com/priyeshsrivastava/pdfparser-agent",
        "Documentation": "https://github.com/priyeshsrivastava/pdfparser-agent#readme",
    },
) 