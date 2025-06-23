from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from ..models.models import DailyMarketingData

class OptimizationService:
    def __init__(self, db: Session):
        self.db = db
        self.min_spend_constraints = {
            'Google Ads': 1000,  # Minimum daily spend
            'Meta Ads': 500,
            'Email': 10,
            'TikTok': 200,
            'Affiliate': 0  # Commission-based
        }
    
    def optimize_budget(self, total_budget: float, constraints: Optional[Dict] = None) -> Dict:
        """Optimize budget allocation across channels to maximize revenue"""
        # Get historical performance data
        channel_curves = self._calculate_response_curves()
        
        # Apply custom constraints if provided
        if constraints:
            for channel, constraint in constraints.items():
                if 'min' in constraint:
                    self.min_spend_constraints[channel] = constraint['min']
        
        # Run optimization
        optimal_allocation = self._run_optimization(total_budget, channel_curves)
        
        # Calculate projected results
        projected_revenue = self._calculate_projected_revenue(optimal_allocation, channel_curves)
        current_revenue = self._calculate_current_revenue()
        revenue_lift = projected_revenue - current_revenue
        
        return {
            'total_budget': total_budget,
            'optimized_allocation': optimal_allocation,
            'projected_revenue': round(projected_revenue, 2),
            'current_revenue': round(current_revenue, 2),
            'revenue_lift': round(revenue_lift, 2),
            'roi_improvement': round((revenue_lift / total_budget) * 100, 2),
            'recommendations': self._generate_recommendations(optimal_allocation)
        }
    
    def _calculate_response_curves(self) -> Dict:
        """Calculate response curves for each channel"""
        # Get last 90 days of data for curve fitting
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        data = self.db.query(DailyMarketingData).filter(
            DailyMarketingData.date >= start_date
        ).all()
        
        df = pd.DataFrame([{
            'date': d.date,
            'channel': d.channel,
            'spend': float(d.spend),
            'revenue': float(d.revenue),
            'conversions': d.conversions
        } for d in data])
        
        curves = {}
        
        for channel in df['channel'].unique():
            channel_data = df[df['channel'] == channel]
            
            # Fit logarithmic response curve: revenue = a * log(spend + 1) + b
            # This models diminishing returns
            if len(channel_data) > 10:
                X = channel_data['spend'].values
                y = channel_data['revenue'].values
                
                # Remove outliers
                q1 = np.percentile(y, 25)
                q3 = np.percentile(y, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                mask = (y >= lower_bound) & (y <= upper_bound)
                X_clean = X[mask]
                y_clean = y[mask]
                
                if len(X_clean) > 5:
                    # Fit the curve
                    coefficients = np.polyfit(np.log(X_clean + 1), y_clean, 1)
                    
                    curves[channel] = {
                        'type': 'logarithmic',
                        'a': coefficients[0],  # Slope
                        'b': coefficients[1],  # Intercept
                        'saturation_point': self._find_saturation_point(coefficients),
                        'current_spend': channel_data['spend'].mean(),
                        'current_revenue': channel_data['revenue'].mean()
                    }
        
        return curves
    
    def _find_saturation_point(self, coefficients: np.ndarray) -> float:
        """Find the spend level where marginal returns become negligible"""
        a, b = coefficients
        
        # Saturation point is where derivative < 0.1 (10 cents return per dollar spent)
        # derivative of a*log(x+1)+b is a/(x+1)
        # a/(x+1) = 0.1, so x = a/0.1 - 1
        
        if a > 0:
            saturation = (a / 0.1) - 1
            return min(saturation, 20000)  # Cap at 20k daily spend
        else:
            return 10000  # Default if curve fitting fails
    
    def _run_optimization(self, total_budget: float, channel_curves: Dict) -> Dict:
        """Run the optimization algorithm"""
        channels = list(channel_curves.keys())
        n_channels = len(channels)
        
        # Initial allocation (current spend levels)
        x0 = [channel_curves[ch]['current_spend'] for ch in channels]
        
        # Normalize to match total budget
        current_total = sum(x0)
        if current_total > 0:
            x0 = [x * total_budget / current_total for x in x0]
        
        # Objective function (negative because we minimize)
        def objective(x):
            total_revenue = 0
            for i, channel in enumerate(channels):
                if channel in channel_curves:
                    curve = channel_curves[channel]
                    # Revenue = a * log(spend + 1) + b
                    revenue = curve['a'] * np.log(x[i] + 1) + curve['b']
                    total_revenue += revenue
                else:
                    # Simple linear model if no curve
                    total_revenue += x[i] * 5  # Assume 5x ROAS
            
            return -total_revenue  # Negative for minimization
        
        # Constraints
        constraints = []
        
        # Total budget constraint
        constraints.append({
            'type': 'eq',
            'fun': lambda x: np.sum(x) - total_budget
        })
        
        # Minimum spend constraints
        bounds = []
        for channel in channels:
            min_spend = self.min_spend_constraints.get(channel, 0)
            max_spend = min(total_budget * 0.5, channel_curves[channel].get('saturation_point', total_budget))
            bounds.append((min_spend, max_spend))
        
        # Run optimization
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        # Format results
        optimal_allocation = {}
        for i, channel in enumerate(channels):
            optimal_allocation[channel] = round(result.x[i], 2)
        
        return optimal_allocation
    
    def _calculate_projected_revenue(self, allocation: Dict, channel_curves: Dict) -> float:
        """Calculate projected revenue from optimal allocation"""
        total_revenue = 0
        
        for channel, spend in allocation.items():
            if channel in channel_curves:
                curve = channel_curves[channel]
                revenue = curve['a'] * np.log(spend + 1) + curve['b']
                total_revenue += revenue
            else:
                # Fallback to historical average ROAS
                total_revenue += spend * 5
        
        return total_revenue
    
    def _calculate_current_revenue(self) -> float:
        """Calculate current revenue baseline"""
        # Last 30 days average
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        result = self.db.query(
            func.sum(DailyMarketingData.revenue)
        ).filter(
            DailyMarketingData.date >= start_date
        ).scalar()
        
        daily_avg = float(result or 0) / 30
        return daily_avg  # Daily revenue
    
    def _generate_recommendations(self, optimal_allocation: Dict) -> List[Dict]:
        """Generate actionable recommendations based on optimization results"""
        recommendations = []
        
        # Get current spend levels
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        current_spend = self.db.query(
            DailyMarketingData.channel,
            func.avg(DailyMarketingData.spend).label('avg_spend')
        ).filter(
            DailyMarketingData.date >= start_date
        ).group_by(DailyMarketingData.channel).all()
        
        current_spend_dict = {row.channel: float(row.avg_spend) for row in current_spend}
        
        for channel, optimal_spend in optimal_allocation.items():
            current = current_spend_dict.get(channel, 0)
            difference = optimal_spend - current
            
            if abs(difference) > 100:  # Significant change
                if difference > 0:
                    action = "increase"
                    icon = "📈"
                else:
                    action = "decrease"
                    icon = "📉"
                
                recommendations.append({
                    'channel': channel,
                    'action': action,
                    'current_spend': round(current, 2),
                    'recommended_spend': round(optimal_spend, 2),
                    'change_amount': round(abs(difference), 2),
                    'change_percentage': round((difference / current * 100), 2) if current > 0 else 0,
                    'priority': 'high' if abs(difference) > 1000 else 'medium',
                    'message': f"{icon} {action.capitalize()} {channel} spend by ${abs(difference):.0f}/day"
                })
        
        # Sort by priority and change amount
        recommendations.sort(key=lambda x: (x['priority'] == 'high', x['change_amount']), reverse=True)
        
        return recommendations
    
    def simulate_scenarios(self, scenarios: List[Dict]) -> Dict:
        """Simulate multiple budget scenarios"""
        results = []
        
        for scenario in scenarios:
            optimization_result = self.optimize_budget(
                scenario['total_budget'],
                scenario.get('constraints')
            )
            
            results.append({
                'scenario_name': scenario['name'],
                'total_budget': scenario['total_budget'],
                'projected_revenue': optimization_result['projected_revenue'],
                'revenue_lift': optimization_result['revenue_lift'],
                'roi': round(optimization_result['projected_revenue'] / scenario['total_budget'], 2),
                'allocation': optimization_result['optimized_allocation']
            })
        
        return {
            'scenarios': results,
            'best_scenario': max(results, key=lambda x: x['roi'])['scenario_name'],
            'comparison_chart': self._prepare_scenario_comparison(results)
        }
    
    def _prepare_scenario_comparison(self, scenarios: List[Dict]) -> Dict:
        """Prepare data for scenario comparison visualization"""
        return {
            'labels': [s['scenario_name'] for s in scenarios],
            'budgets': [s['total_budget'] for s in scenarios],
            'revenues': [s['projected_revenue'] for s in scenarios],
            'roi_values': [s['roi'] for s in scenarios]
        }
    
    def get_diminishing_returns_analysis(self) -> Dict:
        """Analyze diminishing returns for each channel"""
        curves = self._calculate_response_curves()
        analysis = {}
        
        for channel, curve in curves.items():
            # Calculate efficiency at different spend levels
            spend_levels = np.linspace(100, curve['saturation_point'], 20)
            marginal_returns = []
            
            for i in range(1, len(spend_levels)):
                spend_diff = spend_levels[i] - spend_levels[i-1]
                revenue_at_i = curve['a'] * np.log(spend_levels[i] + 1) + curve['b']
                revenue_at_i_minus_1 = curve['a'] * np.log(spend_levels[i-1] + 1) + curve['b']
                revenue_diff = revenue_at_i - revenue_at_i_minus_1
                
                marginal_roas = revenue_diff / spend_diff if spend_diff > 0 else 0
                marginal_returns.append({
                    'spend': round(spend_levels[i], 2),
                    'marginal_roas': round(marginal_roas, 2)
                })
            
            analysis[channel] = {
                'saturation_point': round(curve['saturation_point'], 2),
                'current_spend': round(curve['current_spend'], 2),
                'efficiency_status': self._get_efficiency_status(curve['current_spend'], curve['saturation_point']),
                'marginal_returns_curve': marginal_returns
            }
        
        return analysis
    
    def _get_efficiency_status(self, current_spend: float, saturation_point: float) -> str:
        """Determine efficiency status based on current spend vs saturation"""
        ratio = current_spend / saturation_point
        
        if ratio < 0.7:
            return "under-invested"
        elif ratio < 0.9:
            return "efficient"
        elif ratio < 1.1:
            return "near-saturation"
        else:
            return "over-saturated"