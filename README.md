# SFD Population Proportion Calculator

A Python tool that automates the calculation of the **proportion of the population using each sanitation system (p)** for the **Sustainable Sanitation Alliance (SuSanA) Shit Flow Diagram (SFD)** matrix. The tool processes household survey data and calculates the **"p" values** required for the SuSanA SFD Graphic Generator.

## Why this tool?

Calculating the population proportion ("p") for each sanitation system manually using Excel pivot tables can be time-consuming and repetitive, especially for large household datasets. This tool was developed to automate that process, reducing hours of manual data analysis to just a few seconds while minimizing the risk of calculation errors.

## How to use

The tool requires a household survey dataset containing the questionnaire fields referenced in the code. These datasets are typically exported from **KoboCollect** or similar digital survey platforms.

1. Export your household survey data (e.g., from KoboCollect).
2. Update the file path in the Python script to point to your dataset.
3. Run the script.
4. The tool will automatically calculate the **"p" values** for each sanitation system represented in the dataset.

An example household dataset is included in this repository to demonstrate the required input format.
