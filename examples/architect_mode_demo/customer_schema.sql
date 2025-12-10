-- Customer Table Schema
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    subscription_start_date DATE,
    subscription_type VARCHAR(50),
    is_active BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample data
INSERT INTO customers VALUES 
(1, 'John Doe', 'john@example.com', '010-1234-5678', '2020-01-15', 'Premium', true, NOW()),
(2, 'Jane Smith', 'jane@example.com', '010-2345-6789', '2021-06-20', 'Basic', true, NOW()),
(3, 'Bob Wilson', 'bob@example.com', '010-3456-7890', '2019-03-10', 'Premium', false, NOW());
