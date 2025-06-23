from app.models.database import Base, engine, SessionLocal
from app.models.models import DailyMarketingData, Campaign, ExternalFactor, AttributionResult
from app.utils.data_generator import MMMDataGenerator
from datetime import datetime
import pandas as pd

def seed_database():
    # Create a database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        db.query(DailyMarketingData).delete()
        db.query(Campaign).delete()
        db.query(ExternalFactor).delete()
        db.query(AttributionResult).delete()
        db.commit()
        
        # Initialize the data generator
        generator = MMMDataGenerator()
        
        # Generate 2 years of marketing data ending yesterday
        print("Generating marketing data...")
        # End at yesterday, start 2 years before
        end_date = datetime.now() - pd.Timedelta(days=1)
        start_date = end_date - pd.Timedelta(days=730)
        marketing_data = generator.generate_two_years_data(start_date)
        
        # Insert marketing data
        print(f"Inserting {len(marketing_data)} rows of marketing data...")
        for _, row in marketing_data.iterrows():
            record = DailyMarketingData(
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
            db.add(record)
        
        # Generate and insert external factors
        print("Generating external factors...")
        external_factors = generator.generate_external_factors(start_date)
        print(f"Inserting {len(external_factors)} rows of external factors...")
        for _, row in external_factors.iterrows():
            record = ExternalFactor(
                date=row['date'],
                is_holiday=row['is_holiday'],
                holiday_name=row['holiday_name'],
                competitor_activity=row['competitor_activity'],
                seasonality_index=row['seasonality_index']
            )
            db.add(record)
        
        # Generate and insert campaigns
        print("Generating campaigns...")
        campaigns = generator.generate_campaigns(marketing_data)
        print(f"Inserting {len(campaigns)} campaigns...")
        for _, row in campaigns.iterrows():
            record = Campaign(
                channel=row['channel'],
                campaign_name=row['campaign_name'],
                start_date=row['start_date'],
                end_date=row['end_date'],
                budget=row['budget'],
                campaign_type=row['campaign_type']
            )
            db.add(record)
        
        # Commit all changes
        db.commit()
        print("\nDatabase seeded successfully!")
        
        # Print summary
        print("\nData Summary:")
        print(f"- Marketing Data: {db.query(DailyMarketingData).count()} records")
        print(f"- Campaigns: {db.query(Campaign).count()} records")
        print(f"- External Factors: {db.query(ExternalFactor).count()} records")
        
        # Show sample data by channel
        print("\nSample data by channel:")
        for channel in ['Google Ads', 'Meta Ads', 'Email', 'TikTok', 'Affiliate']:
            channel_data = db.query(DailyMarketingData).filter(
                DailyMarketingData.channel == channel
            ).limit(5).all()
            if channel_data:
                latest = channel_data[0]
                print(f"\n{channel}:")
                print(f"  Date: {latest.date}, Spend: ${latest.spend}, Revenue: ${latest.revenue}")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()