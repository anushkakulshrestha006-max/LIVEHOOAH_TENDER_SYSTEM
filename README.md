# LIVEHOOAH Tender Intelligence System

This is a project I built during my internship at Livehooah Technology Pvt Ltd.

The main idea was to automate the process of finding and organizing relevant government and private tenders for the company. Instead of checking different tender websites manually, the system searches for tenders, extracts their details, checks their relevance, removes duplicates and saves the useful ones to Google Sheets.

I also built a Streamlit dashboard to view the collected opportunities and some basic analytics.

## What it does

- Searches for relevant tenders
- Extracts information from web pages and PDF documents
- Checks tenders based on Livehooah's services
- Gives a relevance score and priority
- Removes duplicate tenders
- Saves qualified opportunities to Google Sheets
- Shows the results through a Streamlit dashboard

## Tech Stack

- Python
- Google Search / SERP API
- PDF and HTML extraction
- Google Sheets
- Streamlit
- Pytest

## How it works

Search
  ↓
Extract tender details
  ↓
Check relevance
  ↓
Qualify and prioritize
  ↓
Remove duplicates
  ↓
Save to Google Sheets
  ↓
View on Dashboard
