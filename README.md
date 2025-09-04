# Gipuzkoa Mobility Open Visualizer

This application provides a web-based interface for exploring and cataloguing mobility-related datasets in Gipuzkoa. It includes interactive maps, dataset visualizations, and a custom AI-powered map generation tool to support the development of a mobility data space in the region.

Developed using Python and Dash.

---

## Project Structure

```
aplicación/
│
├── app.py ← Main entry point: home page + data catalogue module
├── assets/ ← CSS styles, logos, and images
├── data/ ← Data files organized by source
├── modules/ ← Independent modules by data type (interactive map components except rsu and dgt3)
│   ├── dgt/  
│   ├── dgt3/ ← Module used to access data from DGT 3.0 Platform in Data Catalogue
│   ├── udala/  
│   ├── attg/
│   ├── gasolineras/ 
│   ├── estaciones/ 
│   ├── aemet/ 
│   ├── rsu/ ← Module used to access data from RSU DB (CEIT owner) in Data Catalogue
│   └── custom/ ← AI-powered custom map generator
```
---

## Getting Started

### 1. Clone the repository

```bash
git clone https://https://github.com/mzuazolaarr/dataspace
cd mobility-data-platform/aplicación
```

### 2. Install dependencies (Make sure you are using Python 3.9 or later.)

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```
Then open your browser and go to: http://127.0.0.1:8050/

❗ **WARNING:** You must insert your own API key from [OpenRouter.ai](https://openrouter.ai) in `custom_mapa.py`.
