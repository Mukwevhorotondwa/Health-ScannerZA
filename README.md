# 🇿🇦 Health Scanner - SA Product Health Rating Web App

[![Health Score](https://img.shields.io/badge/Health_Score-0--100-blue)](/)
[![Project Status](https://img.shields.io/badge/Status-MVP_Complete-green)](/)
[![Tech Stack](https://img.shields.io/badge/Stack-Python%20%7C%20Flask%20%7C%20VanillaJS-orange)](/)

## 📋 Executive Summary

**Health Scanner** is a lightweight web application designed to help South African consumers make informed decisions about the products they purchase. By scanning or entering product barcodes, users receive instant **health scores (0-100)** based on nutritional content, additives, and other health factors. The application aims to promote healthier eating habits by making nutritional information easily accessible and understandable.

## ✨ Project Vision & Goals

* **Simplicity:** Present complex nutritional data in an easy-to-understand health score.
* **Local Focus:** Prioritize South African products and brands (14+ sample products pre-loaded).
* **Open Source:** Build a community-driven, transparent health platform.

---

## 🏗️ Technical Architecture

The project follows a simple client-server architecture:

* **Frontend:** Pure HTML5, CSS3, Vanilla JavaScript (Single Page Application).
* **Backend (API):** Python 3.8+, Flask, Flask-CORS.
* **Database:** SQLite3 (single file: `healthscanner.db`).

### Health Scoring Algorithm Highlights

The score starts at 100 and is adjusted based on nutrient density per 100g:

* **Deductions:** High Sugar (max -30), High Salt (max -25), High Saturated Fat (max -20), and Additives (-3 each).
* **Bonuses:** Fiber (max +5) and Protein (max +5).

---

## 🚀 Getting Started (Run Locally)

To run the Health Scanner API and Frontend on your local machine:
