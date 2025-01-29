# Relayy MVP Demo

## Description
This repository is a demo of the Relayy MVP functionality. This app will simulate the allocation and distribution of 
equity and appreciation for both the home owner and investors.  This app will provide an interface through which this 
distribution can be simulated based on:
- Initial Property Value
- Current Mortgage Interest Rate
- Desired Home Down Payment

A forecasted home appreciation value for the next five years was created using a Holt-Winters time-series forecasting
model and is based on data from the [Federal Housing Finance Agency](https://www.fhfa.gov/data/hpi/datasets?tab=regional-hpi).

The fully functional app can be found here: [Relayy Demo](https://payable-lisa-true-data-science-710894a2.koyeb.app/)


While this app was built for web deployment, it can also be launched locally as follows:
### Installation
1. **Clone the repository**:
   ```sh
   git clone https://github.com/Csmith715/relayyDemo.git
   cd relayyDemo
   
2. **Set up the virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate

3. **Install the dependencies:**
   ```sh
   pip install -r requirements.txt
   
### Usage
1. **Run the application**
   ```sh
   python app.py
   
2. **Access the application through your browser at:** http://localhost:5000.

