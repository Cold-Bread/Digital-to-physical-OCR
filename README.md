#Backend Setup:

cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# or
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload
----------------------------------------------------------------------------------------------------------------------------------

 #Frontend Setup:

# install Node.js (if not already installed)
# https://nodejs.org/en/download

cd frontend
npm install
npm run dev
----------------------------------------------------------------------------------------------------------------------------------
#run backend:
# uvicorn backend.main:app --reload

#api is live at http://localhost:8000
# test endpoints http://localhost:8000/docs



#run frontend:
# hosted on http://localhost:5173

#app is hot reload, to see changes run
# npm run build
