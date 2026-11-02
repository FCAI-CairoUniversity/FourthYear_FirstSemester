/* ==============================================================================
CAIRO UNIVERSITY - FACULTY OF COMPUTING AND ARTIFICIAL INTELLIGENCE (FCAI)
Information Systems Department
SIS418: Selected Topics in Data Engineering - Spring 2026
Lab 1: Indexing
============================================================================== */

-- Check if the database already exists; if not, create it
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'FCAI_DB')
BEGIN
    CREATE DATABASE FCAI_DB;
END
GO

-- Switch to the database
USE FCAI_DB;
GO

-- Create the Employees table.
CREATE TABLE Employees (
    EmployeeID INT IDENTITY(1,1),
    Name NVARCHAR(50),
    Department NVARCHAR(50),
    Salary INT
);
GO

-- Insert data into the Employees table.
INSERT INTO Employees (Name, Department, Salary) 
VALUES 
('Ali', 'Finance', 8500), 
('Sara', 'IT', 12000), 
('Omar', 'Finance', 9400), 
('Mona', 'HR', 7700), 
('Laila', 'IT', 11000), 
('Youssef', 'Marketing', 9500);
GO

-- Create a clustered index on EmployeeID.
CREATE CLUSTERED INDEX IX_Employees_EmployeeID 
ON Employees(EmployeeID);
GO

-- Create a non-clustered index on Salary 
CREATE NONCLUSTERED INDEX IX_Employees_Department 
ON Employees(Department);
GO

-- Create a composite index on two columns 
CREATE NONCLUSTERED INDEX IX_Employees_Department_Salary 
ON Employees (Department, Salary);
GO

-- View all indexes using sp_helpindex.
EXEC sp_helpindex 'Employees';
GO

-- Drop all indexes
/*
DROP INDEX IX_Employees_EmployeeID ON Employees;
GO

DROP INDEX IX_Employees_Department ON Employees;
GO

DROP INDEX IX_Employees_Department_Salary ON Employees;
GO
*/