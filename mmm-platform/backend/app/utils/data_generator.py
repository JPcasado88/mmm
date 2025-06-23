import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple

class MMMDataGenerator:
    def __init__(self):
        self.channels = {
            'Google Ads': {
                'base_cpm': 25,
                'conversion_rate': 0.022,
                'seasonality_responsive': True,
                'diminishing_returns_point': 5000,  # daily spend
                'avg_order_value': 85
            },
            'Meta Ads': {
                'base_cpm': 18,
                'conversion_rate': 0.018,
                'ios14_impact': True,  # -30% performance post Apr 2021
                'best_days': ['Thu', 'Fri', 'Sat'],
                'avg_order_value': 75
            },
            'Email': {
                'base_cost': 500,  # monthly fixed
                'conversion_rate': 0.045,
                'best_days': ['Tue', 'Thu'],
                'list_growth_rate': 0.02,  # 2% monthly
                'avg_order_value': 95
            },
            'TikTok': {
                'base_cpm': 10,
                'conversion_rate': 0.015,
                'high_growth': True,  # improving over time
                'younger_audience': True,
                'avg_order_value': 65
            },
            'Affiliate': {
                'commission_rate': 0.08,  # 8% of revenue
                'base_conversions': 50,
                'growth_tied_to_brand': True,
                'avg_order_value': 80
            }
        }
        
        self.holidays = {
            'Black Friday': {'date': 'november-fourth-friday', 'multiplier': 3.0},
            'Cyber Monday': {'date': 'november-fourth-monday', 'multiplier': 2.5},
            'Christmas': {'date': '12-25', 'multiplier': 1.8},
            'New Year': {'date': '01-01', 'multiplier': 1.3},
            'Valentine\'s Day': {'date': '02-14', 'multiplier': 1.5},
            'Memorial Day': {'date': 'may-last-monday', 'multiplier': 1.4},
            'July 4th': {'date': '07-04', 'multiplier': 1.3},
            'Labor Day': {'date': 'september-first-monday', 'multiplier': 1.4}
        }
    
    def get_seasonality_index(self, date: datetime) -> float:
        """Calculate seasonality index based on date"""
        month = date.month
        day_of_week = date.weekday()
        
        # Base seasonality by month
        monthly_seasonality = {
            1: 0.9,   # January - post-holiday slump
            2: 0.95,  # February
            3: 1.0,   # March
            4: 1.05,  # April
            5: 1.1,   # May
            6: 0.8,   # June - summer slump begins
            7: 0.6,   # July - deep summer slump
            8: 0.65,  # August - still slow
            9: 0.9,   # September - picking up
            10: 1.1,  # October - pre-holiday
            11: 1.5,  # November - Black Friday
            12: 1.4   # December - holiday season
        }
        
        # Day of week factors (0 = Monday, 6 = Sunday)
        dow_factors = {
            0: 0.9,   # Monday
            1: 0.95,  # Tuesday
            2: 1.0,   # Wednesday
            3: 1.1,   # Thursday
            4: 1.15,  # Friday
            5: 1.05,  # Saturday
            6: 0.85   # Sunday
        }
        
        return monthly_seasonality.get(month, 1.0) * dow_factors.get(day_of_week, 1.0)
    
    def is_holiday(self, date: datetime) -> Tuple[bool, str, float]:
        """Check if date is a holiday and return multiplier"""
        # Black Friday check
        if date.month == 11 and date.weekday() == 4:  # Thursday
            november_first = datetime(date.year, 11, 1)
            days_since_first = (date - november_first).days
            if 21 <= days_since_first <= 27:  # 4th Thursday
                return True, 'Black Friday', 3.0
        
        # Cyber Monday (Monday after Black Friday)
        if date.month == 11 and date.weekday() == 0:  # Monday
            november_first = datetime(date.year, 11, 1)
            days_since_first = (date - november_first).days
            if 24 <= days_since_first <= 30:  # Monday after 4th Thursday
                return True, 'Cyber Monday', 2.5
        
        # Fixed date holidays
        date_str = f"{date.month:02d}-{date.day:02d}"
        for holiday, info in self.holidays.items():
            if isinstance(info['date'], str) and '-' in info['date'] and len(info['date']) == 5:
                if date_str == info['date']:
                    return True, holiday, info['multiplier']
        
        return False, None, 1.0
    
    def apply_diminishing_returns(self, spend: float, channel: str) -> float:
        """Apply diminishing returns curve to spend effectiveness"""
        if channel not in self.channels:
            return 1.0
        
        dr_point = self.channels[channel].get('diminishing_returns_point', float('inf'))
        if spend <= dr_point:
            return 1.0
        else:
            # Logarithmic decay after diminishing returns point
            excess_ratio = spend / dr_point
            return 1.0 / (1 + np.log(excess_ratio))
    
    def generate_channel_data(self, date: datetime, channel: str, base_daily_budget: float) -> Dict:
        """Generate data for a specific channel on a specific date"""
        channel_config = self.channels[channel]
        
        # Calculate actual spend with some randomness
        seasonality = self.get_seasonality_index(date)
        is_hol, holiday_name, holiday_mult = self.is_holiday(date)
        
        # Adjust spend based on seasonality and holidays
        spend_multiplier = seasonality * (holiday_mult if is_hol else 1.0)
        
        # Add channel-specific adjustments
        if channel == 'TikTok' and channel_config.get('high_growth'):
            # TikTok grows from 5% to 20% of spend over 2 years
            days_since_start = (date - datetime(2022, 1, 1)).days
            growth_factor = 1 + (days_since_start / 730) * 3  # 4x growth over 2 years
            spend_multiplier *= growth_factor
        
        if channel == 'Meta Ads' and channel_config.get('ios14_impact'):
            # iOS14 impact after April 2021
            if date >= datetime(2021, 4, 26):
                spend_multiplier *= 0.7  # 30% reduction in efficiency
        
        # Calculate daily spend
        daily_spend = base_daily_budget * spend_multiplier * (1 + random.uniform(-0.1, 0.1))
        
        # Calculate impressions based on CPM
        if 'base_cpm' in channel_config:
            cpm = channel_config['base_cpm'] * (1 + random.uniform(-0.2, 0.2))
            impressions = int((daily_spend / cpm) * 1000)
        else:
            impressions = 0
        
        # Calculate clicks (CTR varies by channel)
        ctr_rates = {
            'Google Ads': 0.02,
            'Meta Ads': 0.015,
            'Email': 0.025,
            'TikTok': 0.01,
            'Affiliate': 0.03
        }
        ctr = ctr_rates.get(channel, 0.02) * (1 + random.uniform(-0.3, 0.3))
        clicks = int(impressions * ctr) if impressions > 0 else 0
        
        # Apply diminishing returns to conversion rate
        dr_factor = self.apply_diminishing_returns(daily_spend, channel)
        base_conv_rate = channel_config.get('conversion_rate', 0.02)
        effective_conv_rate = base_conv_rate * dr_factor * seasonality
        
        # Add day-of-week boost for certain channels
        if date.strftime('%a') in channel_config.get('best_days', []):
            effective_conv_rate *= 1.2
        
        # Calculate conversions
        conversions = int(clicks * effective_conv_rate) if clicks > 0 else 0
        
        # Special handling for affiliate (based on overall brand strength)
        if channel == 'Affiliate':
            base_conversions = channel_config['base_conversions']
            conversions = int(base_conversions * seasonality * holiday_mult * (1 + random.uniform(-0.2, 0.2)))
        
        # Calculate revenue
        aov = channel_config.get('avg_order_value', 80) * (1 + random.uniform(-0.1, 0.1))
        revenue = conversions * aov
        
        # Special handling for affiliate spend (commission-based)
        if channel == 'Affiliate':
            daily_spend = revenue * channel_config['commission_rate']
        
        # Split between new and returning customers
        new_customer_rate = 0.4 if channel != 'Email' else 0.1  # Email has mostly returning
        new_customers = int(conversions * new_customer_rate)
        returning_customers = conversions - new_customers
        
        return {
            'date': date,
            'channel': channel,
            'spend': round(daily_spend, 2),
            'impressions': impressions,
            'clicks': clicks,
            'conversions': conversions,
            'revenue': round(revenue, 2),
            'new_customers': new_customers,
            'returning_customers': returning_customers
        }
    
    def generate_two_years_data(self, start_date: datetime = None) -> pd.DataFrame:
        """Generate 2 years of marketing data with realistic patterns"""
        if start_date is None:
            start_date = datetime(2022, 1, 1)
        
        end_date = start_date + timedelta(days=730)  # 2 years
        
        # Base daily budgets by channel
        base_budgets = {
            'Google Ads': 6200,
            'Meta Ads': 3500,
            'Email': 17,  # ~$500/month
            'TikTok': 500,  # Will grow over time
            'Affiliate': 0  # Commission-based
        }
        
        all_data = []
        current_date = start_date
        
        while current_date <= end_date:
            for channel in self.channels.keys():
                daily_data = self.generate_channel_data(
                    current_date, 
                    channel, 
                    base_budgets.get(channel, 1000)
                )
                all_data.append(daily_data)
            
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(all_data)
        return df
    
    def generate_external_factors(self, start_date: datetime = None) -> pd.DataFrame:
        """Generate external factors data"""
        if start_date is None:
            start_date = datetime(2022, 1, 1)
        
        end_date = start_date + timedelta(days=730)
        
        factors_data = []
        current_date = start_date
        
        while current_date <= end_date:
            is_hol, holiday_name, _ = self.is_holiday(current_date)
            seasonality = self.get_seasonality_index(current_date)
            
            # Simulate competitor activity
            competitor_activity = None
            if random.random() < 0.05:  # 5% chance of competitor activity
                activities = [
                    "Major competitor sale",
                    "New competitor launch", 
                    "Competitor TV campaign",
                    "Industry event"
                ]
                competitor_activity = random.choice(activities)
            
            factors_data.append({
                'date': current_date,
                'is_holiday': is_hol,
                'holiday_name': holiday_name,
                'competitor_activity': competitor_activity,
                'seasonality_index': round(seasonality, 2)
            })
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(factors_data)
    
    def generate_campaigns(self, marketing_df: pd.DataFrame) -> pd.DataFrame:
        """Generate campaign metadata based on marketing data"""
        campaigns = []
        campaign_id = 1
        
        # Generate campaigns for each channel
        for channel in self.channels.keys():
            channel_data = marketing_df[marketing_df['channel'] == channel]
            
            # Create quarterly campaigns
            for year in [2022, 2023]:
                for quarter in range(1, 5):
                    start_month = (quarter - 1) * 3 + 1
                    start_date = datetime(year, start_month, 1)
                    if quarter < 4:
                        end_date = datetime(year, start_month + 2, 30)
                    else:
                        end_date = datetime(year, 12, 31)
                    
                    # Calculate budget from actual spend
                    quarter_data = channel_data[
                        (channel_data['date'] >= start_date) & 
                        (channel_data['date'] <= end_date)
                    ]
                    
                    if len(quarter_data) > 0:
                        budget = quarter_data['spend'].sum()
                        
                        # Determine campaign type based on quarter
                        if quarter in [1, 3]:
                            campaign_type = 'awareness'
                        elif quarter == 4:
                            campaign_type = 'conversion'  # Q4 holiday focus
                        else:
                            campaign_type = 'retention'
                        
                        campaigns.append({
                            'id': campaign_id,
                            'channel': channel,
                            'campaign_name': f"{channel} - {year} Q{quarter} - {campaign_type.title()}",
                            'start_date': start_date,
                            'end_date': end_date,
                            'budget': round(budget, 2),
                            'campaign_type': campaign_type
                        })
                        campaign_id += 1
        
        return pd.DataFrame(campaigns)

if __name__ == "__main__":
    # Test the generator
    generator = MMMDataGenerator()
    
    print("Generating 2 years of marketing data...")
    marketing_data = generator.generate_two_years_data()
    print(f"Generated {len(marketing_data)} rows of marketing data")
    print("\nSample data:")
    print(marketing_data.head())
    
    print("\n\nGenerating external factors...")
    external_factors = generator.generate_external_factors()
    print(f"Generated {len(external_factors)} rows of external factors")
    
    print("\n\nGenerating campaigns...")
    campaigns = generator.generate_campaigns(marketing_data)
    print(f"Generated {len(campaigns)} campaigns")
    print("\nSample campaigns:")
    print(campaigns.head())