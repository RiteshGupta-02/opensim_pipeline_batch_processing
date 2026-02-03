Title: Human Sitting to Walking Transitions: A Motion Capture Dataset


Institution: Motion Capture Laboratory, School of Engineering, Monash University Malaysia


Authors and Emails:
Chamalka Kenneth Perera: chamalka.perera@monash.edu 
Zakia Hussain: zakia.hussain@monash.edu 
Min Khant: min.khant@monash.edu 
Alpha Agape Gopalai: alpha.agape@monash.edu 
Darwin Gouwanda: darwin.gouwanda@monash.edu


Year of Data Collection: 2023


Keywords: Sit-to-walk, Standing, IMU, Surface electromyography, Timed-up-and-go test, MVC


Funding: This work is supported by the Ministry of Higher Education, Malaysia under the 
project number: FRGS/1/2022/TK07/MUSM/02/2 and  FRGS/1/2020/TK0/MUSM/02/2.


License: This dataset is published under the Creative Commons Attribution License (CC BY 
4.0).


File Formats:
- Database: ZIP
- Subject details: CSV
- KOOS survey: PDF
- Motion capture and force plates: C3D
- Surface electromyography and inertial measurement unit: CSV


--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Dataset Structure and Naming Convention: 

The root directory contains a 'Subject Details.csv' file for all subject details, and each base folder contains the respective dataset files for a single subject. 
These are identified by subject number from S01 (subject 01) to S65 (subject 65). 


Each subject folder contains two sub-folders (1) Mocap and (2) EMG and IMU, and a 'KOOS.pdf' file.
 

(1) Mocap subfolder contains the lower body motion capture data, in C3D format, obtained for the respective subject during the sit-to-walk data collection trials. 
Motion capture was recorded using a Qualisys (Sweden) Motion Capture system and three Bertec (USA) force plates. 
This folder contains a 'static.c3d' file for the static motion capture recoding and five sit-to-walk repetitions for the subject, denoted with the repetition number: 'stw1.c3d', 'stw2.c3d', 'stw3.c3d', 'stw4.c3d' and 'stw5.c3d'.

The C3D format files can be read, edited and visualized in open source toolkit Motion kinematic and kinetic analyzer (Mokka) (https://biomechanical-toolkit.github.io/mokka/). Other C3D parsers include the Biomechanics ToolKit (BTK) (http://biomechanical-toolkit.github.io/)and the ezc3d package (https://github.com/pyomeca/ezc3d). 

(2) EMG and IMU subfolder contains the surface electromyography (EMG) and inertial measurement unit (IMU) data collectively per file, in CSV format, collected during the sit-to-walk data collection trials. 
EMG and IMU data were collected using a Delsys (USA) Trigno Wireless System with Trigo Avantii and Trigno Duo sensors. 
This folder contains three files for the maximum voluntary contraction (MVC) for each muscle group denoted as 'mvc_hamstrings.csv', 'mvc_quadriceps.csv' and 'mvc_shank.csv' and five sit-to-walk repetitions for the subject, denoted with the repetition number: 'stw1.csv', 'stw2.csv', 'stw3.csv', 'stw4.csv'and 'stw5.csv'.


--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Dataset File Contents and Column Headings:

1. Subject Details.csv: contains data entries for all 65 subjects with data columns (in order) for Subject Number, Sex, Age (Years), Weight (kg), Height (m), Dominant Leg.


2. KOOS.pdf: contains the individual qualitative subject responses for the Knee Injury and Osteoarthritis Outcome Score (KOOS) survey.


3. C3D Mocap files:
	a. static.c3d: contains the stationary static motion capture recoding with 36 passive retro-reflective markers in C3D format.
	
	b. stw1.c3d to stw5.c3d: contains the dynamic motion capture recordings with 32 passive retro-reflective markers in C3D format.
	
	c. These files contain raw marker trajectories, force plate data (ground reaction force, center of pressure and moment) along with settings and system information.


4. EMG and IMU files:

	a. mvc_hamstrings.csv: contains the maximal voluntary contraction EMG data for the Biceps Femoris and Semitendinosus.

	b. mvc_quadriceps.csv: contains the maximal voluntary contraction EMG data for the Rectus Femoris, Vastus Lateralis and Vastus Medialis.  
	
	c. mvc_shank.csv: contains the maximal voluntary contraction EMG data for the Tibialis Anterior, Gastrocnemius Lateralis and Gastrocnemius Medialis.  
	
	d. stw1.csv to stw5.csv: contains the EMG and IMU data from the eight Delsys Trigno sensors.
	
	e. Each file contains data entries from all 8 sensors with data columns of EMG followed by IMU acceleration (ACC X, ACC Y and ACC Z) and angular velocity (GYRO X, GYRO Y and GYRO Z). The sampling frequencies of each column are  provided in the column headers. The sensor order by column, based on muscle placement is Tibialis Anterior, Gastrocnemius (Lateralis and Medialis), Rectus Femoris, Quads (Vastus Lateralis and Medialis), Semitendinosus, Bicep Femoris, Foot IMU and Trunk IMU.

	f. Due to the different sampling frequencies in SEMG and IMU data, there will be different lengths of the time series in the provided CSV files.
