/* ==============================================================================
CAIRO UNIVERSITY - FACULTY OF COMPUTING AND ARTIFICIAL INTELLIGENCE (FCAI)
Information Systems Department
SIS418: Selected Topics in Data Engineering - Spring 2026
Lab 3: Query Tuning and Execution Plans
============================================================================== */

-- 0. Preparation / Setup
-- Switch to the AdventureWorks database context
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'AdventureWorks2019')
BEGIN
    USE AdventureWorks2019;
END
ELSE IF EXISTS (SELECT * FROM sys.databases WHERE name = 'AdventureWorks')
BEGIN
    USE AdventureWorks;
END
GO

-- Enable STATISTICS IO and TIME to monitor I/O cost and CPU/execution time
-- Note: Remember to turn on "Include Actual Execution Plan" in SSMS (Ctrl + M)
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
GO

-- ==============================================================================
-- 1. Table Scan vs. Clustered Index Scan
-- Concept:
-- - Table Scan: Reads every row in a heap (table without a clustered index).
-- - Clustered Index Scan: Reads all rows in clustered-index physical order.
-- ==============================================================================

-- Create a test copy of the table without indexes (Heap Table)
IF OBJECT_ID('Sales.SalesOrderDetail_new', 'U') IS NOT NULL
DROP TABLE Sales.SalesOrderDetail_new;

SELECT *
INTO Sales.SalesOrderDetail_new
FROM Sales.SalesOrderDetail;
GO

-- Table Scan (Heap Table - no index exists)
SELECT *
FROM Sales.SalesOrderDetail_new;
GO

-- Clustered Index Scan (Original table - clustered index exists)
SELECT *
FROM Sales.SalesOrderDetail;
GO

-- ==============================================================================
-- 2. ORDER BY / GROUP BY Optimization Using Clustered Indexes
-- Concept: If data is already physically sorted by a clustered index,
-- SQL Server avoids an explicit Sort operator in the execution plan.
-- ==============================================================================

-- Querying Heap table with ORDER BY (Requires explicit Sort operator)
SELECT *
FROM Sales.SalesOrderDetail_new
ORDER BY SalesOrderID;
GO

-- Querying Clustered Index table with ORDER BY (No explicit Sort required)
SELECT *
FROM Sales.SalesOrderDetail
ORDER BY SalesOrderID;
GO

-- ==============================================================================
-- 3. Index Seek and Nonclustered Indexes (Covering Index)
-- Concept: Index Seek navigates directly to matching rows.
-- INCLUDE clause creates a covering index to eliminate costly Key Lookups.
-- ==============================================================================

-- Query without index (Results in a Table Scan on heap)
SELECT ProductID, CarrierTrackingNumber, OrderQty
FROM Sales.SalesOrderDetail_new
WHERE CarrierTrackingNumber = '4911-403C-98';
GO

-- Create Nonclustered Covering Index on CarrierTrackingNumber
CREATE NONCLUSTERED INDEX IX_SalesOrderDetail_CarrierTrackingNumber
ON Sales.SalesOrderDetail (CarrierTrackingNumber)
INCLUDE (ProductID, OrderQty);
GO

-- Query using Nonclustered Index (Results in an Index Seek with NO Key Lookup)
SELECT ProductID, CarrierTrackingNumber, OrderQty
FROM Sales.SalesOrderDetail
WHERE CarrierTrackingNumber = '4911-403C-98';
GO

-- ==============================================================================
-- 4. Avoid SELECT *
-- Concept: Selecting only required columns reduces I/O, memory footprint,
-- and allows query optimizer to leverage covering nonclustered indexes.
-- ==============================================================================

-- Inefficient: Uses SELECT * (Cannot be covered by NCI, requires Key Lookup / Clustered Index Scan)
SELECT *
FROM Sales.SalesOrderDetail
WHERE CarrierTrackingNumber = '4911-403C-98';
GO

-- Efficient: Selects only required columns (Covered by NCI)
SELECT CarrierTrackingNumber, ProductID
FROM Sales.SalesOrderDetail
WHERE CarrierTrackingNumber = '4911-403C-98';
GO

-- ==============================================================================
-- 5. Limit Data Retrieval (TOP with ORDER BY)
-- Concept: Early stopping with TOP when supported by a matching index.
-- ==============================================================================

-- Create index to support ORDER BY on LineTotal
CREATE NONCLUSTERED INDEX IX_SalesOrderDetail_LineTotal
ON Sales.SalesOrderDetail (LineTotal)
INCLUDE (ProductID);
GO

-- Optimized TOP query (Stops reading after retrieving first 10 rows)
SELECT TOP 10 SalesOrderID, ProductID, LineTotal
FROM Sales.SalesOrderDetail
ORDER BY LineTotal;
GO

-- ==============================================================================
-- 6. Aggregation Performance (Hash Aggregate vs. Stream Aggregate)
-- Concept:
-- - Hash Aggregate: Memory intensive, used for unsorted input.
-- - Stream Aggregate: Fast and efficient, used for pre-sorted input.
-- ==============================================================================

-- Without supporting index (Executes as Hash Aggregate + Clustered Index Scan)
SELECT ProductID, SUM(LineTotal) AS TotalLineTotal
FROM Sales.SalesOrderDetail
GROUP BY ProductID;
GO

-- Create nonclustered index on GROUP BY key (ProductID) including aggregate column (LineTotal)
CREATE NONCLUSTERED INDEX IX_SalesOrderDetail_ProductID
ON Sales.SalesOrderDetail (ProductID)
INCLUDE (LineTotal);
GO

-- With supporting index (Switches operator to Stream Aggregate)
SELECT ProductID, SUM(LineTotal) AS TotalLineTotal
FROM Sales.SalesOrderDetail
GROUP BY ProductID;
GO

-- ==============================================================================
-- 7. Functions on Indexed Columns (SARGability)
-- Concept: Applying functions to columns in the WHERE clause breaks SARGability
-- and forces a Scan instead of an Index Seek.
-- ==============================================================================

-- Non-SARGable: LEFT() function prevents Index Seek (Results in Scan)
SELECT *
FROM Production.Product
WHERE LEFT(Name, 1) = 'A';
GO

-- SARGable: Rewrite predicate using LIKE to enable Index Seek
SELECT ProductID, Name
FROM Production.Product
WHERE Name LIKE 'A%';
GO

-- ==============================================================================
-- 8. Join Optimization
-- Concept: Indexes on join keys and filtered columns enable efficient join
-- algorithms (e.g., Nested Loops or Merge Join vs Hash Match).
-- ==============================================================================

-- Multi-table join query
SELECT soh.SalesOrderID, soh.OrderDate, sod.ProductID, sod.LineTotal
FROM Sales.SalesOrderHeader soh
JOIN Sales.SalesOrderDetail sod
ON soh.SalesOrderID = sod.SalesOrderID
WHERE soh.OrderDate >= '2014-01-01'
AND sod.LineTotal > 1000;
GO

-- Create supporting nonclustered indexes for joined tables
CREATE NONCLUSTERED INDEX IX_SalesOrderHeader_OrderDate
ON Sales.SalesOrderHeader (OrderDate);
GO

-- Re-run query after index creation to compare plan and join algorithm
SELECT soh.SalesOrderID, soh.OrderDate, sod.ProductID, sod.LineTotal
FROM Sales.SalesOrderHeader soh
JOIN Sales.SalesOrderDetail sod
ON soh.SalesOrderID = sod.SalesOrderID
WHERE soh.OrderDate >= '2014-01-01'
AND sod.LineTotal > 1000;
GO

-- ==============================================================================
-- 9. Composite Indexes for Multi-Condition Filters & Column Ordering Rules
-- Rules:
-- 1. Equality filters (=) first.
-- 2. Range / Inequality filters (<, >, BETWEEN) in order of selectivity.
-- 3. ORDER BY / GROUP BY columns next.
-- 4. INCLUDED columns for coverage.
-- ==============================================================================

-- Query filtering on multiple ranges (ListPrice & Weight)
SELECT ProductID, Name, ProductNumber, ListPrice, Weight
FROM Production.Product
WHERE ListPrice BETWEEN 500 AND 2000
AND Weight > 10;
GO

-- Composite Index: ListPrice is more selective (101 rows) than Weight (126 rows), so ListPrice is 1st
CREATE NONCLUSTERED INDEX IX_Product_ListPrice_Weight
ON Production.Product (ListPrice, Weight)
INCLUDE (ProductNumber, Name);
GO

-- Re-run multi-condition query with composite index
SELECT ProductID, Name, ProductNumber, ListPrice, Weight
FROM Production.Product
WHERE ListPrice BETWEEN 500 AND 2000
AND Weight > 10;
GO

-- Generic Example: Equality condition first, Inequality condition second
/*
SELECT *
FROM Orders
WHERE CustomerID = 100
AND OrderDate >= '2026-01-01';

CREATE NONCLUSTERED INDEX IX_Orders
ON Orders (CustomerID, OrderDate);
*/
GO

-- ==============================================================================
-- 10. Cleanup Operations
-- Restores database to original state by removing created tables and indexes.
-- ==============================================================================

-- Drop test heap table
DROP TABLE IF EXISTS Sales.SalesOrderDetail_new;
GO

-- Drop nonclustered indexes created during lab
DROP INDEX IF EXISTS IX_SalesOrderDetail_CarrierTrackingNumber ON Sales.SalesOrderDetail;
DROP INDEX IF EXISTS IX_SalesOrderDetail_LineTotal ON Sales.SalesOrderDetail;
DROP INDEX IF EXISTS IX_SalesOrderDetail_ProductID ON Sales.SalesOrderDetail;
DROP INDEX IF EXISTS IX_SalesOrderHeader_OrderDate ON Sales.SalesOrderHeader;
DROP INDEX IF EXISTS IX_Product_ListPrice_Weight ON Production.Product;
GO

-- Turn off statistics options
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO