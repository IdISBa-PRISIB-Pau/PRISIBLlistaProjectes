# PRISIB Llista Projectes

<img src="./00%20Imatges/Logo_idisba.png" alt="Idisba" height="120px" float="left" /> 
<img src="./00%20Imatges/Logo_ssib.png" alt="SSIB" height="120px" float="left"/> 


### Dades del projecte
- Codi: P
- Data inici:15/04/2024
- Tipus de tasca: 
- Sol·licitud: 
- Contacte:
	- Nom: Pau Pericàs
	- Correu: gds@gfgdfmm.llgdfff
- Projecte:
	- Titol: 
	- Protocol:
	- Referencia:
	- Dictamen CEIB:
- Documentació associada:
- Objectes creats a BD:
- Scripts generats:

### Resum
This project is a Python-based application designed to scan through a directory of repositories, extract specific information from each repository, and write this information to a CSV file. The application is built with a GUI using the Tkinter library, allowing users to easily interact with the application.  
#### Key Features
1. Repository Scanning: The application scans through a directory of repositories. For each repository, it extracts specific information from the README file and checks for the presence of certain files.  
2. Information Extraction: The application extracts the Codi and Data inici fields from the README file in each repository. It also checks for the presence of PDF files with specific prefixes and whether these PDFs are signed. Additionally, it checks for the presence of a specific .xlsx file.  
3. CSV Output: The application writes the extracted information to a CSV file. Each row in the CSV file corresponds to a repository and contains the repository name, the extracted Codi and Data inici values, the statuses of the PDF files, and whether the .xlsx file was found.  
4. GUI Interface: The application includes a GUI built with Tkinter. The GUI allows users to specify the directory to scan and the output CSV file.  
#### Code Structure
The code is divided into two main files: main.py and UI.py.  
. main.py contains the core functionality of the application. It includes functions for scanning the repositories, extracting information from the README files, checking for the presence of specific files, and writing the extracted information to a CSV file.  
. UI.py contains the code for the GUI. It includes functions for browsing for a directory and a file, and a function for running the script when the "Run Script" button is clicked.  
#### Usage
To use the application, run UI.py. Use the "Browse" buttons to select the directory to scan and the output CSV file. Then, click the "Run Script" button to start the scanning process. The application will scan through the repositories in the specified directory and write the extracted information to the specified CSV file.


Per desenvolupar aquest codi i la seva documentació s'ha fet servir GitHub Copilot.

## Anàlisi

## Desenvolupament

## Entregues

## Incidències

## Referències

## Comunicacions  
