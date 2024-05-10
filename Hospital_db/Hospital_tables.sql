CREATE TABLE Admin (
  Admin_ID INT Primary key,
  A_Name varchar(100),
  A_Phone varchar(100),
  A_Address varchar(100),
  A_Email varchar(100),
  Password varchar(100)
);

CREATE TABLE Radiologist (
  D_ID INT Primary key,
  D_Name varchar(100),
  D_Gender varchar(100),
  D_Phone varchar(100),
  D_Address varchar(100),
  D_Email varchar(100),
  D_Password varchar(100)
);
CREATE TABLE Patient (
  P_ID INT Primary key,
  P_Phone varchar(100),
  P_Name varchar(100),
  P_Gender varchar(100),
  P_Age INT,
  P_Address varchar(100),
  P_Time varchar(100),
  P_Password varchar(100),
  P_Email varchar(100)
);


CREATE TABLE Radiology_Equipment (
  Device_ID INT Primary key,
  Commission_Date varchar(100),
  Maintenance_Date varchar(100)
);
CREATE TABLE Report (
  ID_Report INT Primary key,
  ID_Patient INT REFERENCES Patient(P_ID),
  ID_Doctor INT REFERENCES Radiologist(D_ID),
  R_Time varchar(100),
  R_Result varchar(100),
  ID_Device INT REFERENCES Radiology_Equipment(Device_ID),
  R_Image varchar(100),
  Billing INT
);

