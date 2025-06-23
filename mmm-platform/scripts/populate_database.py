import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.utils.data_generator import MMMDataGenerator
from backend.app.models.database import engine, SessionLocal
from backend.app.models.models import Base, DailyMarketingData, Campaign, ExternalFactor
from sqlalchemy import text
import pandas as pd
from datetime import datetime

def clear_tables(db):
    """Clear existing data from tables"""
    try:
        db.execute(text("TRUNCATE TABLE daily_marketing_data, campaigns, external_factors, attribution_results CASCADE"))
        db.commit()
        print("Tables cleared successfully")
    except Exception as e:
        print(f"Error clearing tables: {e}")
        db.rollback()

def populate_marketing_data(db, df):
    """Populate daily_marketing_data table"""
    print("Populating marketing data...")
    
    for _, row in df.iterrows():
        data = DailyMarketingData(
            date=row['date'],
            channel=row['channel'],
            spend=row['spend'],
            impressions=row['impressions'],
            clicks=row['clicks'],
            conversions=row['conversions'],
            revenue=row['revenue'],
            new_customers=row['new_customers'],
            returning_customers=row['returning_customers']
        )
        db.add(data)
    
    db.commit()
    print(f"Added {len(df)} rows to daily_marketing_data")

def populate_campaigns(db, df):
    """Populate campaigns table"""
    print("Populating campaigns...")
    
    for _, row in df.iterrows():
        campaign = Campaign(
            channel=row['channel'],
            campaign_name=row['campaign_name'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            budget=row['budget'],
            campaign_type=row['campaign_type']
        )
        db.add(campaign)
    
    db.commit()
    print(f"Added {len(df)} campaigns")

def populate_external_factors(db, df):
    """Populate external_factors table"""
    print("Populating external factors...")
    
    for _, row in df.iterrows():
        factor = ExternalFactor(
            date=row['date'],
            is_holiday=row['is_holiday'],
            holiday_name=row['holiday_name'],
            competitor_activity=row['competitor_activity'],
            seasonality_index=row['seasonality_index']
        )
        db.add(factor)
    
    db.commit()
    print(f"Added {len(df)} rows to external_factors")

def main():
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Initialize generator
    generator = MMMDataGenerator()
    
    # Generate data
    print("\nGenerating 2 years of marketing data...")
    marketing_data = generator.generate_two_years_data()
    
    print("Generating external factors...")
    external_factors = generator.generate_external_factors()
    
    print("Generating campaigns...")
    campaigns = generator.generate_campaigns(marketing_data)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_tables(db)
        
        # Populate tables
        populate_marketing_data(db, marketing_data)
        populate_external_factors(db, external_factors)
        populate_campaigns(db, campaigns)
        
        # Print summary statistics
        print("\n=== Data Generation Summary ===")
        print(f"Total rows generated: {len(marketing_data)}")
        print(f"Date range: {marketing_data['date'].min()} to {marketing_data['date'].max()}")
        print(f"\nSpend by channel:")
        channel_summary = marketing_data.groupby('channel').agg({
            'spend': 'sum',
            'revenue': 'sum',
            'conversions': 'sum'
        }).round(2)
        channel_summary['ROAS'] = (channel_summary['revenue'] / channel_summary['spend']).round(2)
        print(channel_summary)
        
        print(f"\nTotal spend: ${marketing_data['spend'].sum():,.2f}")
        print(f"Total revenue: ${marketing_data['revenue'].sum():,.2f}")
        print(f"Overall ROAS: {marketing_data['revenue'].sum() / marketing_data['spend'].sum():.2f}x")
        
        # Save sample data to CSV for inspection
        marketing_data.to_csv('sample_marketing_data.csv', index=False)
        print("\nSample data saved to sample_marketing_data.csv")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()