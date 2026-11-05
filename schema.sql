-- 31th Oct initialize the db
-- Enable TimescaleDB extension if not already enabled
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create a reference table for categories to ensure data integrity
CREATE TABLE spending_categories (
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50) NOT NULL,
    PRIMARY KEY (category, subcategory)
);

-- 2. Insert expanded categories
INSERT INTO spending_categories (category, subcategory) VALUES
('Housing', 'Mortgage or rent'), ('Housing', 'Property taxes'), ('Housing', 'Household repairs'), ('Housing', 'Homeowners association (HOA) fees'), ('Housing', 'Furnishings'),
('Transportation', 'Car payment'), ('Transportation', 'Car warranty'), ('Transportation', 'Gas'), ('Transportation', 'Tires'), ('Transportation', 'Maintenance and oil changes'), ('Transportation', 'Parking fees'), ('Transportation', 'Repairs'), ('Transportation', 'Registration and DMV Fees'), ('Transportation', 'Public transit'), ('Transportation', 'Rideshare/Taxis'), ('Transportation', 'Tolls'),
('Food', 'Groceries'), ('Food', 'Restaurants'), ('Food', 'Coffee shops'),
('Utilities', 'Electricity'), ('Utilities', 'Water'), ('Utilities', 'Garbage'), ('Utilities', 'Phones'), ('Utilities', 'Cable'), ('Utilities', 'Internet'),
('Clothing', 'Adults clothing'), ('Clothing', 'Adults shoes'), ('Clothing', 'Childrens clothing'), ('Clothing', 'Childrens shoes'), ('Clothing', 'Dry cleaning/Laundry'),
('Medical/Healthcare', 'Primary care'), ('Medical/Healthcare', 'Dental care'), ('Medical/Healthcare', 'Specialty care'), ('Medical/Healthcare', 'Urgent care'), ('Medical/Healthcare', 'Medications'), ('Medical/Healthcare', 'Medical devices'), ('Medical/Healthcare', 'Therapy/Mental health'), ('Medical/Healthcare', 'Vision/Contacts'),
('Insurance', 'Health insurance'), ('Insurance', 'Homeowners or renters insurance'), ('Insurance', 'Home warranty or protection plan'), ('Insurance', 'Auto insurance'), ('Insurance', 'Life insurance'), ('Insurance', 'Disability insurance'), ('Insurance', 'Pet insurance'),
('Household Items/Supplies', 'Toiletries'), ('Household Items/Supplies', 'Laundry detergent'), ('Household Items/Supplies', 'Dishwasher detergent'), ('Household Items/Supplies', 'Cleaning supplies'), ('Household Items/Supplies', 'Tools'),
('Personal', 'Gym memberships'), ('Personal', 'Haircuts'), ('Personal', 'Salon services'), ('Personal', 'Cosmetics'), ('Personal', 'Subscriptions'), ('Personal', 'Spa/Massage'),
('Family/Childcare', 'Babysitter'), ('Family/Childcare', 'Daycare/Tuition'), ('Family/Childcare', 'Toys/Activities'),
('Pets', 'Pet food'), ('Pets', 'Vet care'), ('Pets', 'Pet supplies/Toys'),
('Debt', 'Personal loans'), ('Debt', 'Student loans'), ('Debt', 'Credit cards'),
('Retirement', 'Financial planning'), ('Retirement', 'Investing'),
('Education', 'Childrens college'), ('Education', 'Your college'), ('Education', 'School supplies'), ('Education', 'Books'),
('Savings', 'Emergency fund'), ('Savings', 'Big purchases'), ('Savings', 'Other savings'),
('Gifts/Donations', 'Birthday'), ('Gifts/Donations', 'Anniversary'), ('Gifts/Donations', 'Wedding'), ('Gifts/Donations', 'Christmas'), ('Gifts/Donations', 'Special occasion'), ('Gifts/Donations', 'Charities'),
('Entertainment', 'Alcohol and/or bars'), ('Entertainment', 'Games'), ('Entertainment', 'Movies'), ('Entertainment', 'Concerts'), ('Entertainment', 'Vacations'), ('Entertainment', 'Subscriptions'), ('Entertainment', 'Hobbies'),
('Fees/Taxes', 'Bank fees'), ('Fees/Taxes', 'Late fees'), ('Fees/Taxes', 'Income tax'),
('Uncategorized', 'Uncategorized');

-- 3. Create the main spendings table
CREATE TABLE spendings (
    id UUID DEFAULT uuid_generate_v4(),
    time TIMESTAMPTZ NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50) NOT NULL,
    merchant VARCHAR(255),
    description TEXT,
    is_ai_extracted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (category, subcategory) REFERENCES spending_categories(category, subcategory),
    PRIMARY KEY (id, time)
);

-- 4. Convert to a TimescaleDB hypertable partitioned by time (chunk size of 1 month is standard)
SELECT create_hypertable('spendings', 'time', chunk_time_interval => INTERVAL '1 month');




--6th Nov: add category
-- Insert the detailed Earned, Investment, and Passive income categories
INSERT INTO spending_categories (category, subcategory) VALUES
('Earned Income', 'Salary and wages'), 
('Earned Income', 'Tips and commissions'), 
('Earned Income', 'Bonuses'), 
('Earned Income', 'Self-employment income'),
('Earned Income', 'Allowance'),

('Investment Income', 'Stocks'), 
('Investment Income', 'Real estate'), 
('Investment Income', 'Collectibles'), 
('Investment Income', 'Stock options'), 
('Investment Income', 'Businesses'),

('Passive Income', 'Interest'), 
('Passive Income', 'Dividends'), 
('Passive Income', 'Rental income'), 
('Passive Income', 'Royalties');


-- 2. Add the new column to indicate cash flow direction
ALTER TABLE spendings 
ADD COLUMN transaction_type VARCHAR(10) DEFAULT 'EXPENSE';

-- 3. Enforce data integrity so it only accepts 'INCOME' or 'EXPENSE'
ALTER TABLE spendings 
ADD CONSTRAINT check_transaction_type CHECK (transaction_type IN ('INCOME', 'EXPENSE'));