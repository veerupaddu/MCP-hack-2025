#!/usr/bin/env python3
"""
Script to fill in the auto insurance product design document with fictional data
"""

import re
from datetime import datetime

def fill_document(content):
    """Fill in all placeholders with realistic fictional data"""
    
    # Product name and basic info
    content = content.replace("[To be determined]", "TokyoDrive Insurance")
    content = content.replace("[Current Date]", datetime.now().strftime("%B %d, %Y"))
    content = content.replace("[Your Name/Team]", "Product Development Team")
    content = content.replace("[Date]", datetime.now().strftime("%B %d, %Y"))
    content = content.replace("[Author]", "Product Development Team")
    content = content.replace("[Approver Name/Title]", "Chief Product Officer")
    
    # Remove guidance notes
    content = re.sub(r'\*\*\[Guidance:.*?\]\*\*', '', content)
    content = re.sub(r'\[Guidance:.*?\]', '', content)
    
    # Executive Summary - Financial Projections
    content = content.replace("| Policies Written | [X] | [Y] | [Z] |", 
                              "| Policies Written | 5,000 | 25,000 | 60,000 |")
    content = content.replace("| Premium Volume (¥) | [X]M | [Y]M | [Z]M |",
                              "| Premium Volume (¥) | 450M | 2,250M | 5,400M |")
    content = content.replace("| Loss Ratio | [X]% | [Y]% | [Z]% |",
                              "| Loss Ratio | 72% | 68% | 65% |")
    content = content.replace("| Combined Ratio | [X]% | [Y]% | [Z]% |",
                              "| Combined Ratio | 102% | 96% | 93% |")
    content = content.replace("| Net Profit (¥) | [X]M | [Y]M | [Z]M |",
                              "| Net Profit (¥) | -9M | 90M | 378M |")
    
    # Strategic Objectives
    content = content.replace("Achieve [X]% market penetration", "Achieve 2.5% market penetration")
    content = content.replace("Maintain loss ratio below [X]%", "Maintain loss ratio below 70%")
    content = content.replace("Achieve customer satisfaction score of [X]", "Achieve customer satisfaction score of 4.5")
    content = content.replace("[X]% online policy purchases", "75% online policy purchases")
    content = content.replace("[X] repair shops", "150 repair shops")
    
    # Market Size
    content = content.replace("Approximately [X] million registered vehicles", 
                              "Approximately 4.2 million registered vehicles")
    
    # Vehicle Ownership Statistics
    content = content.replace("| Total Registered Vehicles | [X] | As of [Date] |",
                              "| Total Registered Vehicles | 4,200,000 | As of 2024 |")
    content = content.replace("| Passenger Cars | [X] | Percentage: [X]% |",
                              "| Passenger Cars | 3,360,000 | Percentage: 80% |")
    content = content.replace("| Commercial Vehicles | [X] | Percentage: [X]% |",
                              "| Commercial Vehicles | 630,000 | Percentage: 15% |")
    content = content.replace("| Motorcycles | [X] | Percentage: [X]% |",
                              "| Motorcycles | 168,000 | Percentage: 4% |")
    content = content.replace("| Electric/Hybrid Vehicles | [X] | Percentage: [X]% |",
                              "| Electric/Hybrid Vehicles | 42,000 | Percentage: 1% |")
    
    # Age Distribution (fictional but realistic)
    age_data = """| 18-24 | 850,000 | 6.0% | 340,000 |
| 25-34 | 2,100,000 | 15.0% | 1,680,000 |
| 35-44 | 2,800,000 | 20.0% | 2,240,000 |
| 45-54 | 2,500,000 | 17.8% | 2,000,000 |
| 55-64 | 2,200,000 | 15.7% | 1,760,000 |
| 65+ | 3,597,594 | 25.6% | 1,800,000 |"""
    content = re.sub(r'\| 18-24 \| \[X\] \| \[X\]% \| \[X\] \|.*?\| 65\+ \| \[X\] \| \[X\]% \| \[X\] \|',
                     age_data, content, flags=re.DOTALL)
    
    # Income Levels
    income_data = """| 0-3M | 1,200,000 | 16.2% | 35% |
| 3-5M | 2,200,000 | 29.6% | 52% |
| 5-7M | 2,000,000 | 27.0% | 68% |
| 7-10M | 1,500,000 | 20.2% | 78% |
| 10M+ | 521,340 | 7.0% | 85% |"""
    content = re.sub(r'\| 0-3M \| \[X\] \| \[X\]% \| \[X\]% \|.*?\| 10M\+ \| \[X\] \| \[X\]% \| \[X\]% \|',
                     income_data, content, flags=re.DOTALL)
    
    # Employment and Commuting
    content = content.replace("- **Employment Rate**: [X]%", "- **Employment Rate**: 62.5%")
    content = content.replace("- **Average Commute Distance**: [X] km", "- **Average Commute Distance**: 18 km")
    content = content.replace("  - Private Vehicle: [X]%", "  - Private Vehicle: 28%")
    content = content.replace("  - Public Transport: [X]%", "  - Public Transport: 65%")
    content = content.replace("  - Other: [X]%", "  - Other: 7%")
    
    # Vehicle Type Distribution
    content = content.replace("- **Sedans**: [X]%", "- **Sedans**: 45%")
    content = content.replace("- **SUVs**: [X]%", "- **SUVs**: 25%")
    content = content.replace("- **Compact Cars (Kei)**: [X]%", "- **Compact Cars (Kei)**: 18%")
    content = content.replace("- **Luxury Vehicles**: [X]%", "- **Luxury Vehicles**: 8%")
    content = content.replace("- **Commercial Vehicles**: [X]%", "- **Commercial Vehicles**: 4%")
    
    # Vehicle Age Distribution
    vehicle_age = """| 0-3 years | 28% | 2,800,000 |
| 4-7 years | 32% | 1,800,000 |
| 8-12 years | 25% | 1,200,000 |
| 13+ years | 15% | 600,000 |"""
    content = re.sub(r'\| 0-3 years \| \[X\]% \| ¥\[X\] \|.*?\| 13\+ years \| \[X\]% \| ¥\[X\] \|',
                     vehicle_age, content, flags=re.DOTALL)
    
    # Traffic Accident Statistics
    accidents = """| 2020 | 45,230 | 89 | 52,450 | 38,200 |
| 2021 | 43,180 | 85 | 50,120 | 36,800 |
| 2022 | 47,650 | 92 | 54,890 | 39,500 |
| 2023 | 49,320 | 88 | 56,240 | 40,100 |"""
    content = re.sub(r'\| 2020 \| \[X\] \| \[X\] \| \[X\] \| \[X\] \|.*?\| 2023 \| \[X\] \| \[X\] \| \[X\] \| \[X\] \|',
                     accidents, content, flags=re.DOTALL)
    
    content = content.replace("- **Accidents per 1,000 Vehicles**: [X]", "- **Accidents per 1,000 Vehicles**: 11.7")
    content = content.replace("- **Fatal Accidents per 100,000 Vehicles**: [X]", "- **Fatal Accidents per 100,000 Vehicles**: 2.1")
    content = content.replace("- **Average Claim Amount**: ¥[X]", "- **Average Claim Amount**: ¥850,000")
    content = content.replace("- **Average Claim Frequency**: [X]% of policies", "- **Average Claim Frequency**: 8.5% of policies")
    
    # Accident Patterns
    content = content.replace("- Peak Hours (7-9 AM, 5-7 PM): [X]% of accidents", 
                              "- Peak Hours (7-9 AM, 5-7 PM): 42% of accidents")
    content = content.replace("- Daytime (9 AM - 5 PM): [X]% of accidents", 
                              "- Daytime (9 AM - 5 PM): 35% of accidents")
    content = content.replace("- Nighttime (7 PM - 7 AM): [X]% of accidents", 
                              "- Nighttime (7 PM - 7 AM): 23% of accidents")
    content = content.replace("- Weekdays: [X]% of accidents", "- Weekdays: 72% of accidents")
    content = content.replace("- Weekends: [X]% of accidents", "- Weekends: 28% of accidents")
    content = content.replace("- Speeding: [X]%", "- Speeding: 18%")
    content = content.replace("- Distracted Driving: [X]%", "- Distracted Driving: 24%")
    content = content.replace("- Weather-Related: [X]%", "- Weather-Related: 12%")
    content = content.replace("- Other: [X]%", "- Other: 46%")
    
    # Geographic Risk Zones
    risk_zones = """| High | Chiyoda, Chuo, Minato, Shibuya, Shinjuku | 14.2 per 1,000 vehicles | ¥1,200,000 |
| Medium | Meguro, Setagaya, Nakano, Suginami | 10.8 per 1,000 vehicles | ¥850,000 |
| Low | Nerima, Itabashi, Adachi, Outer wards | 8.5 per 1,000 vehicles | ¥650,000 |"""
    content = re.sub(r'\| High \| \[List\] \| \[X\] per 1,000 vehicles \| ¥\[X\] \|.*?\| Low \| \[List\] \| \[X\] per 1,000 vehicles \| ¥\[X\] \|',
                     risk_zones, content, flags=re.DOTALL)
    
    # Competitive Landscape
    competitors = """| Tokio Marine Nichido | 18.5% | Strong brand, extensive network | Premium pricing |
| Sompo Japan | 15.2% | Comprehensive coverage, good service | Competitive |
| Mitsui Sumitomo | 12.8% | Digital innovation, competitive rates | Value-focused |"""
    content = re.sub(r'\| \[Company A\] \| \[X\]% \| \[Strengths\] \| \[Strategy\] \|.*?\| \[Company C\] \| \[X\]% \| \[Strengths\] \| \[Strategy\] \|',
                     competitors, content, flags=re.DOTALL)
    
    # Customer Segments
    content = content.replace("**Size**: Approximately [X]% of Tokyo vehicle owners", 
                              "**Size**: Approximately 32% of Tokyo vehicle owners", count=1)
    content = content.replace("**Size**: Approximately [X]% of Tokyo vehicle owners", 
                              "**Size**: Approximately 38% of Tokyo vehicle owners", count=1)
    content = content.replace("**Size**: Approximately [X]% of Tokyo vehicle owners", 
                              "**Size**: Approximately 18% of Tokyo vehicle owners", count=1)
    content = content.replace("**Size**: Approximately [X]% of Tokyo vehicle owners", 
                              "**Size**: Approximately 12% of Tokyo vehicle owners", count=1)
    
    # Purchase Behavior
    content = content.replace("- **Research Method**: [X]% online research, [X]% agent consultation",
                              "- **Research Method**: 68% online research, 32% agent consultation")
    content = content.replace("- **Decision Factors**: Price ([X]%), Coverage ([X]%), Brand ([X]%), Service ([X]%)",
                              "- **Decision Factors**: Price (35%), Coverage (28%), Brand (22%), Service (15%)")
    content = content.replace("- **Purchase Channel**: Online ([X]%), Agent ([X]%), Phone ([X]%)",
                              "- **Purchase Channel**: Online (55%), Agent (30%), Phone (15%)")
    
    # Usage Patterns
    content = content.replace("- **Annual Mileage**: Average [X] km/year", 
                              "- **Annual Mileage**: Average 12,500 km/year")
    content = content.replace("- **Primary Use**: Commuting ([X]%), Personal ([X]%), Business ([X]%)",
                              "- **Primary Use**: Commuting (45%), Personal (38%), Business (17%)")
    content = content.replace("- **Parking**: Home garage ([X]%), Street parking ([X]%), Paid lot ([X]%)",
                              "- **Parking**: Home garage (42%), Street parking (28%), Paid lot (30%)")
    
    # Premium Ranges
    content = content.replace("**Premium Range**: ¥[X] - ¥[Y] per year", 
                              "**Premium Range**: ¥45,000 - ¥85,000 per year", count=1)
    content = content.replace("**Premium Range**: ¥[X] - ¥[Y] per year", 
                              "**Premium Range**: ¥75,000 - ¥150,000 per year", count=1)
    content = content.replace("**Premium Range**: ¥[X] - ¥[Y] per year", 
                              "**Premium Range**: ¥180,000 - ¥350,000 per year", count=1)
    
    # Digital Features
    content = content.replace("- Complete online purchase in [X] minutes", 
                              "- Complete online purchase in 8 minutes")
    
    # Roadside Assistance
    content = content.replace("- Towing (up to [X] km)", "- Towing (up to 50 km)")
    content = content.replace("Coverage: Up to ¥[X] per incident", 
                              "Coverage: Up to ¥500,000 per incident", count=1)
    content = content.replace("- Coverage: Up to [X] days, ¥[X] per day",
                              "- Coverage: Up to 14 days, ¥8,000 per day")
    content = content.replace("Coverage: Up to ¥[X] per incident",
                              "Coverage: Up to ¥200,000 per incident", count=1)
    
    # Deductibles and Limits
    content = content.replace("- **Deductible**: ¥[X] - ¥[Y] depending on tier",
                              "- **Deductible**: ¥50,000 - ¥200,000 depending on tier")
    content = content.replace("- **Age Restrictions**: Some coverage may not apply to vehicles over [X] years",
                              "- **Age Restrictions**: Some coverage may not apply to vehicles over 15 years")
    
    # Risk Factors
    content = content.replace("- **Rush Hour Risk**: [X]% higher accident rate during peak hours",
                              "- **Rush Hour Risk**: 35% higher accident rate during peak hours")
    content = content.replace("- **Rainy Season** (June-July): [X]% increase in accidents",
                              "- **Rainy Season** (June-July): 18% increase in accidents")
    
    # Vehicle Type Risk - Average Claim Amounts
    vehicle_claims = """| Compact (Kei) | 0.9x | ¥650,000 |
| Sedan | 1.0x | ¥850,000 |
| SUV | 1.1x | ¥1,100,000 |
| Luxury | 1.2x | ¥2,200,000 |
| Sports Car | 1.5x | ¥1,800,000 |
| Commercial | 1.3x | ¥950,000 |
| Motorcycle | 2.0x | ¥720,000 |"""
    content = re.sub(r'\| Compact \(Kei\) \| 0\.9x \| ¥\[X\] \|.*?\| Motorcycle \| 2\.0x \| ¥\[X\] \|',
                     vehicle_claims, content, flags=re.DOTALL)
    
    # Expense Loading
    content = content.replace("- **Acquisition Costs**: [X]% of premium", "- **Acquisition Costs**: 12% of premium")
    content = content.replace("- **Administrative Expenses**: [X]% of premium", "- **Administrative Expenses**: 8% of premium")
    content = content.replace("- **Claims Handling**: [X]% of premium", "- **Claims Handling**: 5% of premium")
    content = content.replace("- **Total Expense Ratio**: [X]% (target: 25-35%)", "- **Total Expense Ratio**: 30% (target: 25-35%)")
    content = content.replace("- **Target Profit Margin**: [X]% (typically 5-10%)", "- **Target Profit Margin**: 7% (typically 5-10%)")
    
    # Premium Examples
    content = content.replace("- **Annual Premium**: ¥[X]", "- **Annual Premium**: ¥98,000", count=1)
    content = content.replace("- **Annual Premium**: ¥[X]", "- **Annual Premium**: ¥125,000", count=1)
    content = content.replace("- **Annual Premium**: ¥[X]", "- **Annual Premium**: ¥285,000", count=1)
    
    # Low Mileage Discount
    content = content.replace("| Low Mileage | 5-15% | Annual mileage < [X] km |",
                              "| Low Mileage | 5-15% | Annual mileage < 8,000 km |")
    content = content.replace("| High Mileage | 5-15% | Annual mileage > [X] km |",
                              "| High Mileage | 5-15% | Annual mileage > 20,000 km |")
    
    # Competitive Pricing
    pricing = """| Basic | ¥65,000 | ¥72,000 | ¥68,000 | ¥70,000 |
| Standard | ¥125,000 | ¥138,000 | ¥132,000 | ¥135,000 |
| Premium | ¥285,000 | ¥320,000 | ¥305,000 | ¥310,000 |"""
    content = re.sub(r'\| Basic \| ¥\[X\] \| ¥\[Y\] \| ¥\[Z\] \| ¥\[W\] \|.*?\| Premium \| ¥\[X\] \| ¥\[Y\] \| ¥\[Z\] \| ¥\[W\] \|',
                     pricing, content, flags=re.DOTALL)
    
    # Regulatory
    content = content.replace("- **Capital Requirements**: Minimum ¥[X] million",
                              "- **Capital Requirements**: Minimum ¥1,000 million")
    content = content.replace("- **Cooling-Off Period**: [X] days to cancel after purchase",
                              "- **Cooling-Off Period**: 14 days to cancel after purchase")
    
    # Service Levels
    content = content.replace("- **Phone Response**: Answer within [X] seconds",
                              "- **Phone Response**: Answer within 30 seconds")
    content = content.replace("- **Email Response**: Within [X] hours",
                              "- **Email Response**: Within 4 hours")
    content = content.replace("- **Chat Response**: Within [X] minutes",
                              "- **Chat Response**: Within 2 minutes")
    content = content.replace("- **Fast Processing**: Target [X] days for simple claims",
                              "- **Fast Processing**: Target 3 days for simple claims")
    content = content.replace("- **Claims Processing**: [X] days for simple claims",
                              "- **Claims Processing**: 3 days for simple claims")
    
    # Partners
    content = content.replace("- **Partners**: [X] certified repair shops in Tokyo",
                              "- **Partners**: 150 certified repair shops in Tokyo")
    
    # Acquisition Channels
    acquisition = """| Online Search | All segments | 3.2% | ¥8,500 |
| Social Media | Young professionals | 2.8% | ¥12,000 |
| Referrals | All segments | 5.5% | ¥3,200 |
| Partners | Business owners | 4.1% | ¥15,000 |
| Agents | Families, seniors | 6.2% | ¥18,000 |"""
    content = re.sub(r'\| Online Search \| All segments \| \[X\]% \| ¥\[X\] \|.*?\| Agents \| Families, seniors \| \[X\]% \| ¥\[X\] \|',
                     acquisition, content, flags=re.DOTALL)
    
    # Financial Projections - Detailed
    # Revenue by Tier
    revenue_tier = """| Basic | ¥135M | ¥675M | ¥1,620M |
| Standard | ¥270M | ¥1,350M | ¥3,240M |
| Premium | ¥45M | ¥225M | ¥540M |"""
    content = re.sub(r'\| Basic \| ¥\[X\]M \| ¥\[Y\]M \| ¥\[Z\]M \|.*?\| Premium \| ¥\[X\]M \| ¥\[Y\]M \| ¥\[Z\]M \|',
                     revenue_tier, content, flags=re.DOTALL)
    
    # Loss Costs
    loss_costs = """| Year 1 | ¥450M | 72% | ¥324M |
| Year 2 | ¥2,250M | 68% | ¥1,530M |
| Year 3 | ¥5,400M | 65% | ¥3,510M |"""
    content = re.sub(r'\| Year 1 \| ¥\[X\]M \| \[Y\]% \| ¥\[Z\]M \|.*?\| Year 3 \| ¥\[X\]M \| \[Y\]% \| ¥\[Z\]M \|',
                     loss_costs, content, flags=re.DOTALL)
    
    # Operating Expenses
    expenses = """| Acquisition Costs | ¥54M | ¥270M | ¥648M |
| Administrative | ¥36M | ¥180M | ¥432M |
| Claims Handling | ¥22.5M | ¥112.5M | ¥270M |
| Technology | ¥18M | ¥45M | ¥108M |
| Marketing | ¥27M | ¥90M | ¥162M |"""
    content = re.sub(r'\| Acquisition Costs \| ¥\[X\]M \| ¥\[Y\]M \| ¥\[Z\]M \|.*?\| Marketing \| ¥\[X\]M \| ¥\[Y\]M \| ¥\[Z\]M \|',
                     expenses, content, flags=re.DOTALL)
    content = content.replace("| **Total Expenses** | **¥[X]M** | **¥[Y]M** | **¥[Z]M** |",
                              "| **Total Expenses** | **¥157.5M** | **¥697.5M** | **¥1,620M** |")
    
    # Loss Ratios by Segment
    segment_loss = """| Young Professionals | 78% | 74% | 70% |
| Families | 68% | 65% | 63% |
| Business Owners | 72% | 69% | 66% |
| Senior Drivers | 70% | 67% | 64% |"""
    content = re.sub(r'\| Young Professionals \| \[X\]% \| \[Y\]% \| \[Z\]% \|.*?\| Senior Drivers \| \[X\]% \| \[Y\]% \| \[Z\]% \|',
                     segment_loss, content, flags=re.DOTALL)
    content = content.replace("| **Overall** | **[X]%** | **[Y]%** | **[Z]%** |",
                              "| **Overall** | **72%** | **68%** | **65%** |")
    
    # Loss Ratios by Coverage
    coverage_loss = """| Liability | 65% | 62% | 60% |
| Comprehensive | 82% | 78% | 75% |
| Personal Injury | 70% | 67% | 64% |"""
    content = re.sub(r'\| Liability \| \[X\]% \| \[Y\]% \| \[Z\]% \|.*?\| Personal Injury \| \[X\]% \| \[Y\]% \| \[Z\]% \|',
                     coverage_loss, content, flags=re.DOTALL)
    
    # Expense Ratios
    expense_ratios = """| Acquisition | 12% | 12% | 12% |
| Administrative | 8% | 8% | 8% |
| Claims Handling | 5% | 5% | 5% |
| Technology | 4% | 2% | 2% |"""
    content = re.sub(r'\| Acquisition \| \[X\]% \| \[Y\]% \| \[Z\]% \|.*?\| Technology \| \[X\]% \| \[Y\]% \| \[Z\]% \|',
                     expense_ratios, content, flags=re.DOTALL)
    content = content.replace("| **Total Expense Ratio** | **[X]%** | **[Y]%** | **[Z]%** |",
                              "| **Total Expense Ratio** | **29%** | **27%** | **27%** |")
    
    # Combined Ratios
    combined = """| Year 1 | 72% | 29% | 101% |
| Year 2 | 68% | 27% | 95% |
| Year 3 | 65% | 27% | 92% |"""
    content = re.sub(r'\| Year 1 \| \[X\]% \| \[Y\]% \| \[Z\]% \|.*?\| Year 3 \| \[X\]% \| \[Y\]% \| \[Z\]% \|',
                     combined, content, flags=re.DOTALL)
    
    # Net Profit
    profit = """| Year 1 | ¥450M | ¥481.5M | ¥-31.5M | -7.0% |
| Year 2 | ¥2,250M | ¥2,227.5M | ¥22.5M | 1.0% |
| Year 3 | ¥5,400M | ¥5,130M | ¥270M | 5.0% |"""
    content = re.sub(r'\| Year 1 \| ¥\[X\]M \| ¥\[Y\]M \| ¥\[Z\]M \| \[W\]% \|.*?\| Year 3 \| ¥\[X\]M \| ¥\[Y\]M \| ¥\[Z\]M \| \[W\]% \|',
                     profit, content, flags=re.DOTALL)
    
    # Break-Even
    content = content.replace("- **Break-Even Policies**: [X] policies", "- **Break-Even Policies**: 18,500 policies")
    content = content.replace("- **Break-Even Premium Volume**: ¥[Y]M", "- **Break-Even Premium Volume**: ¥1,665M")
    content = content.replace("- **Expected Time to Break-Even**: [Z] months", "- **Expected Time to Break-Even**: 14 months")
    
    # Sensitivity Analysis
    content = content.replace("- Higher policy count: [X]% above base", "- Higher policy count: 20% above base")
    content = content.replace("- Lower loss ratio: [Y]% below target", "- Lower loss ratio: 5% below target")
    content = content.replace("- Result: Profit of ¥[Z]M", "- Result: Profit of ¥450M", count=1)
    content = content.replace("- Result: Profit of ¥[X]M", "- Result: Profit of ¥270M")
    content = content.replace("- Lower policy count: [X]% below base", "- Lower policy count: 15% below base")
    content = content.replace("- Higher loss ratio: [Y]% above target", "- Higher loss ratio: 8% above target")
    content = content.replace("- Result: Loss of ¥[Z]M", "- Result: Loss of ¥180M")
    
    # Success Metrics
    content = content.replace("- [X] policies written", "- 5,000 policies written", count=1)
    content = content.replace("- [Y]% customer satisfaction", "- 4.3% customer satisfaction", count=1)
    content = content.replace("- [Z]% online purchase rate", "- 68% online purchase rate", count=1)
    content = content.replace("- Combined ratio < [X]%", "- Combined ratio < 105%", count=1)
    content = content.replace("- [X] policies written (cumulative)", "- 30,000 policies written (cumulative)")
    content = content.replace("- Market share of [Y]%", "- Market share of 0.7%")
    content = content.replace("- Customer retention rate of [Z]%", "- Customer retention rate of 82%")
    content = content.replace("- Combined ratio < [X]%", "- Combined ratio < 95%", count=1)
    content = content.replace("- Customer satisfaction > [Y]%", "- Customer satisfaction > 4.5")
    content = content.replace("- Market share of [Z]%", "- Market share of 1.4%")
    
    # Milestones
    milestones = """| FSA License Approval | Month 8 | [ ] |
| Platform Launch | Month 6 | [ ] |
| First 1,000 Policies | Month 7 | [ ] |
| Break-Even | Month 14 | [ ] |
| 10,000 Policies | Month 12 | [ ] |
| Profitability | Month 18 | [ ] |"""
    content = re.sub(r'\| FSA License Approval \| Month \[X\] \| \[ \] \|.*?\| Profitability \| Month \[X\] \| \[ \] \|',
                     milestones, content, flags=re.DOTALL)
    
    # Human Resources
    hr = """| Management | 8 | 12 | 15 |
| Underwriting | 12 | 20 | 28 |
| Claims | 15 | 25 | 35 |
| Customer Service | 20 | 35 | 50 |
| Technology | 10 | 15 | 20 |
| Marketing | 8 | 12 | 15 |"""
    content = re.sub(r'\| Management \| \[X\] \| \[Y\] \| \[Z\] \|.*?\| Marketing \| \[X\] \| \[Y\] \| \[Z\] \|',
                     hr, content, flags=re.DOTALL)
    content = content.replace("| **Total** | **[X]** | **[Y]** | **[Z]** |",
                              "| **Total** | **73** | **119** | **163** |")
    
    # Capital Requirements
    content = content.replace("- Initial capital: ¥[X]M", "- Initial capital: ¥1,000M")
    content = content.replace("- Operating capital: ¥[Y]M", "- Operating capital: ¥500M")
    content = content.replace("- Reserve requirements: ¥[Z]M", "- Reserve requirements: ¥1,200M")
    content = content.replace("- **Total Capital Needed**: ¥[W]M", "- **Total Capital Needed**: ¥2,700M")
    content = content.replace("- **Minimum Capital**: ¥[X]M (FSA requirement)", 
                              "- **Minimum Capital**: ¥1,000M (FSA requirement)")
    content = content.replace("- **Solvency Margin**: Maintain [X]% above minimum",
                              "- **Solvency Margin**: Maintain 20% above minimum")
    
    # Reinsurance Partners
    reinsurance = """- Tokio Marine Re: Catastrophic coverage, excess of loss
- Swiss Re: Quota share (20%), stop loss protection
- Munich Re: Large claim excess coverage"""
    content = re.sub(r'- \[Reinsurer A\]: \[Coverage type\].*?- \[Reinsurer C\]: \[Coverage type\]',
                     reinsurance, content, flags=re.DOTALL)
    
    return content

if __name__ == "__main__":
    # Read the template
    with open("docs/tokyo_auto_insurance_product_design.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fill in the data
    filled_content = fill_document(content)
    
    # Write the filled version
    with open("docs/tokyo_auto_insurance_product_design_filled.md", "w", encoding="utf-8") as f:
        f.write(filled_content)
    
    print("✓ Document filled with fictional data")
    print("✓ Saved to: docs/tokyo_auto_insurance_product_design_filled.md")

