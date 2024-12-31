# Twitter Bot for Real Estate Recommendations

## Overview
This project involves the development of a **Twitter/X bot** designed to autonomously promote real estate properties in **Istanbul, Turkey**. By leveraging **data analytics** and **machine learning**, the bot identifies the best-value properties, generates engaging tweets, and posts them to Twitter/X. The goal is to attract potential buyers and investors by showcasing high-value real estate listings in an appealing manner. 

The bot account can be reached at: https://x.com/_RealEstateBot.

---

## Key Objectives

- **Property Value Assessment**: Analyze and rank properties based on their value/cost ratio.
- **Content Creation**: Generate engaging and concise property descriptions for tweets using AI.
- **Twitter Automation**: Automate the process of selecting, drafting, and posting tweets.
- **User Engagement**: Enhance interaction and attract followers through visually appealing and well-structured content.

---

## Features

### Data Integration and Analysis
- **Web Scraping**: Automatically fetches real estate data daily from Istanbul's top real estate platforms.
- **Google Cloud Storage**: Securely stores and updates scraped data in a centralized bucket.
- **Machine Learning Models**: Employs predictive models to identify undervalued properties.

### Tweet Crafting
- **Natural Language Processing**: Uses OpenAI’s GPT API to transform property details into engaging, human-like tweets.
- **Dynamic Tweet Schedules**: Posts tweets at randomized intervals to maintain engagement and avoid predictability.

### Automation
- **Daily Workflows**:
  - Fetch fresh property data.
  - Update the predictive model for ranking listings.
  - Post selected listings automatically.
- **Error Handling**: Implements retry mechanisms for resilience against temporary failures.


---

## Architecture

### Google Cloud Integration
- **Storage**: Google Cloud Storage manages real estate datasets and processed results.
- **Scalability**: Cloud-based architecture ensures reliable data handling and accessibility.

### Machine Learning
- **Models**: Random Forest, Gradient Boosting, XGBoost and other model types have been tested for value prediction.
    
- **Feature Engineering**: A significant effort has been made in feature engineering to improve the model's predictive performance. Below is a detailed overview of the feature engineering process and features that have been tried:
    
    - **District-Level Features**: Several district-based features have been integrated, such as:
        
        - **Population Density**: The number of people per square kilometer in each district.
            
        - **Population Count**: Total population of each district.
            
        - **Population Growth Rate**: Yearly growth rate of the population in each district.
            
        - **Socio-Demographic and Socio-Economic Scores**: These scores represent socio-demographic and socio-economic conditions in each district, which provide insights into the living standards and quality of the area.
            
        - **Healthcare Accessibility**: Distance to various healthcare facilities such as pharmacies, family health centers, and hospitals.
            
        - **Social Assistance Information**: Number of households in each district receiving or not receiving social assistance.
            
        - **Average Household Size (m²)**: Average gross and net household sizes in each district.
            
    - **Property-Level Features**: Features directly related to property listings, including:
        
        - **Room Count, Bath Count, and Floor Information**: Basic property features such as the number of rooms, bathrooms, and floor details.
            
        - **Net and Gross Area**: The net and gross sizes of the property in square meters.
            
        - **Location Features**: Latitude, longitude, distance to the sea, distance to malls, and other amenities.
            
        - **Amenity Scores**: Presence of amenities like pools, balconies, and security, represented as binary features.
            
        - **Sentiment Analysis of Descriptions**: Sentiment analysis of property descriptions to understand if positive or compelling language impacts property value (Tested).
            
        - **Keyword Analysis**: Specific keywords in descriptions (e.g., "urgent", "close to metro") were used as binary features to capture the effect of specific selling points.
            
    - **Interaction Features**: Combinations of features that could capture non-linear relationships, such as:
        
        - **Room-to-Bathroom Ratio**: To capture the balance between rooms and bathrooms.
            
        - **Age-to-Floor Ratio**: To see how building age relates to the number of floors.
            
    - **Geospatial Clustering**: Properties were clustered based on geographic coordinates to create a categorical "location cluster" feature that captures regional trends better than latitude and longitude alone.

- **Performance Metrics**: Models are evaluated based on Mean Squared Error (MSE), Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and R² score.


### Twitter Bot Workflow
1. **Web Scraping**:
   - Extracts property data daily.
   - Manages changes in listings (e.g., closed or updated properties).
2. **Modeling**:
   - Predicts undervalued properties using trained models.
   - Dynamically updates based on the latest data.
3. **Tweeting**:
   - Crafts tweets using GPT API with a focus on Turkish real estate.
   - Posts at randomized times for authenticity.

---

## Getting Started

### Prerequisites
- **Python** 3.8+
- **Google Cloud SDK**
- **Twitter Developer Account** for API access
- **OpenAI API key**

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mhsendur/RealEstateTweetBot
   cd RealEstateTweetBot/src
   ```

2. Set up your Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure API credentials:
   - Create a `credentials.py` file with the following variables:
     ```python
     # Twitter API
     consumer_key = "your_consumer_key"
     consumer_secret = "your_consumer_secret"
     access_token = "your_access_token"
     access_token_secret = "your_access_token_secret"
     client_id = "your_client_id"
     client_secret = "your_client_secret"

     # OpenAI API
     api_key = "your_openai_api_key"
     ```

4. Configure Google Cloud Storage:
   - Set up a Google Cloud project.
   - Create a bucket for storing property data.
   - Grant appropriate permissions for the storage service.

5. Run the bot:
   ```bash
   python main.py
   ```

---

## Machine Learning and Analytics

### Models
- **Random Forest**: Primary model for value prediction.
- **Gradient Boosting**: Backup model for comparison.

### Feature Engineering
- **District-level**: Population density, growth, and socio-economic scores.
- **Property-level**: Room count, amenities, and proximity to key landmarks.
- **Sentiment Analysis**: Evaluates listing descriptions for compelling language.

### Performance Metrics
- **Accuracy**: Measures prediction reliability.
- **Engagement**: Monitors tweet performance (likes, retweets, impressions).

---

## Runtime Workflow

1. **Daily Property Scraping**:
   - Collects and updates real estate data at 2 AM GMT every day.
   - Uploads the latest dataset to Google Cloud Storage.

2. **Modeling**:
   - Retrains the model daily with fresh data.
   - Predicts and ranks 100 properties based on value.

3. **Tweet Scheduling**:
   - Randomly selects the top listings for the day.
   - Posts 3–4 tweets at randomized intervals. **Randomization is done to avoid spam-like behavior on the platform, factors such as tweet post time & image count of the post are random.**
   - Ensures no duplicate or closed listings are posted.

4. **Tweet Content**:
   - Generates visually appealing and informative tweets with OpenAI.
   - Includes price, highlights, and a compelling call-to-action.

5. **Error Handling**:
   - Retries failed actions (e.g., API errors).
   - Skips closed or unavailable listings.

---

## Contributors
- **Mustafa Harun Sendur**
- **Melih Cihan Kiziltoprak**
- **Ceren Sahin**
- **Dila Karatas**

---

## Future Improvements
- **Enhanced Engagement**: Experiment with different tweet styles and hashtags to boost visibility.
- **Geospatial Insights**: Integrate maps for location visualization.
- **Advanced Analytics**: Build dashboards for real-time performance monitoring.

> *This project demonstrates the potential of automation and AI in real estate marketing, developed for educational purposes.*

