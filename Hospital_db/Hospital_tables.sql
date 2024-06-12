CREATE TABLE Admin (
                       Admin_ID INT Primary key,
                       A_Name varchar(100),
                       A_Phone varchar(13),
                       A_Address varchar(100),
                       A_Email varchar(100),
                       Password varchar(100)
);
create table radiologist
(
    d_id       integer generated always as identity (minvalue 1000 maxvalue 1999)
        primary key,
    d_name     varchar(100) not null,
    d_gender   varchar(100),
    d_phone    varchar(100),
    d_address  varchar(100),
    d_email    varchar(100),
    d_password varchar(100)
);
create table patient
(
    id              integer generated always as identity (minvalue 2000 maxvalue 2999)
        primary key,
    phone           varchar(100),
    gender          varchar(100),
    age             integer,
    address         varchar(100),
    time            varchar(100),
    password        varchar(100),
    email           varchar(100),
    profile_picture varchar(200),
    scans           varchar(200),
    fname           varchar,
    lname           varchar
);

create table radiology_equipment
(
    device_id        integer generated always as identity (minvalue 4000 maxvalue 4999)
        primary key,
    commission_date  varchar(100),
    maintenance_date varchar(100),
    device_name      varchar not null
);
create table appointments
(
    a_id        integer generated always as identity (minvalue 3000 maxvalue 3999)
        primary key,
    p_id        integer
        references patient,
    d_id        integer     not null
        references radiologist,
    device_id   integer     not null
        references radiology_equipment,
    date        varchar(15) not null,
    device_name varchar,
    d_name      varchar
);
CREATE TABLE Treats (
                        P_ID INT,
                        Device_ID INT,
                        FOREIGN KEY (P_ID) REFERENCES Patient(ID),
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
                             FOREIGN KEY (P_ID) REFERENCES Patient(ID),
                             FOREIGN KEY (D_ID) REFERENCES Radiologist(D_ID),
                             PRIMARY KEY (Admin_ID, Device_ID, D_ID, P_ID)
);
CREATE TABLE Diagnosed_By (
                              Device_ID INT,
                              P_ID INT,
                              FOREIGN KEY (Device_ID) REFERENCES Radiology_Equipment(Device_ID),
                              FOREIGN KEY (P_ID) REFERENCES Patient(ID),
                              PRIMARY KEY (P_ID, Device_ID)
);
create table report
(
    r_id           integer generated always as identity (minvalue 5000 maxvalue 5999)
        primary key,
    p_id           integer
        constraint report_id_patient_fkey
            references patient,
    d_id           integer
        constraint report_id_doctor_fkey
            references radiologist,
    r_time         varchar(100),
    r_result       varchar(100),
    device_id      integer
        constraint report_id_device_fkey
            references radiology_equipment,
    r_scan         varchar(100),
    billing        integer,
    r_study_area   varchar,
    radiation_dose varchar,
    r_findings     varchar
);

