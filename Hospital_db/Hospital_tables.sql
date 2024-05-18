CREATE TABLE Admin (
  Admin_ID INT Primary key,
  A_Name varchar(100),
  A_Phone varchar(13),
  A_Address varchar(100),
  A_Email varchar(100),
  Password varchar(100)
);

CREATE TABLE Radiologist (
  D_ID INT Primary key,
  D_Name varchar(100),
  D_Gender varchar(100),
  D_Phone varchar(13),
  D_Address varchar(100),
  D_Email varchar(100),
  D_Password varchar(100)
);
CREATE TABLE Patient (
  P_ID INT Primary key,
  P_Phone varchar(13),
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
  Commission_Date varchar(8),
  Maintenance_Date varchar(8)
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
CREATE TABLE Treats (
                        P_ID INT,
                        Device_ID INT,
                        FOREIGN KEY (P_ID) REFERENCES Patient(P_ID),
                        FOREIGN KEY (Device_ID) REFERENCES Radiology_Equipment(Device_ID),
                        PRIMARY KEY (P_ID, Device_ID)
);
CREATE TABLE Manipulates (
                             Admin_ID INT,
                             Device_ID INT,
                             D_ID INT,
                             P_ID INT,
                             FOREIGN KEY (Admin_ID) REFERENCES Admin(Admin_ID),
                             FOREIGN KEY (Device_ID) REFERENCES Radiology_Equipment(Device_ID),
                             FOREIGN KEY (P_ID) REFERENCES Patient(P_ID),
                             FOREIGN KEY (D_ID) REFERENCES Radiologist(D_ID),
                             PRIMARY KEY (Admin_ID, Device_ID, D_ID, P_ID)
);
CREATE TABLE Diagnosed_By (
                              Device_ID INT,
                              P_ID INT,
                              FOREIGN KEY (Device_ID) REFERENCES Radiology_Equipment(Device_ID),
                              FOREIGN KEY (P_ID) REFERENCES Patient(P_ID),
                              PRIMARY KEY (P_ID, Device_ID)
);

