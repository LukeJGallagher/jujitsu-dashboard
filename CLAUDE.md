# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JJIF (Ju-Jitsu International Federation) competition data analysis dashboard for Team Saudi. Analyzes athlete profiles, competition brackets, and results with a focus on Asian competitions and Saudi athletes.

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit dashboard
streamlit run dashboard.py
```

## Data Structure

### Key Components

**Dashboard**
- `dashboard.py` - Streamlit app with Team Saudi branding. Shows athlete profiles, competition results, head-to-head analysis, bracket visualization.

**Data Files**
- `event_mappings.json` - Maps event names to event IDs
- `Results/all_profiles.json` - Consolidated athlete profiles
- `Results/all_matches.json` - Match data across events
- `Results/brackets_{id}_{timestamp}.json` - Bracket data with categories and competitors

## Team Saudi Focus

Country codes for filtering: `KSA`, `SAU`, `"Saudi Arabia"`, `السعودية`

## Weight Categories (JJIF)

**Male**: 56kg, 62kg, 69kg, 77kg, 85kg, 94kg, +94kg
**Female**: 48kg, 52kg, 57kg, 63kg, 70kg, +70kg

## Data Directories

```
Results/     - JSON data files
```
