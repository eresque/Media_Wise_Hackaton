from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'])

pdf_directory_path = '/app/backend/data/generated/'
if __name__ == '__main__':
    os.mkdir(pdf_directory_path)

@app.get('/getFile')
async def getFile(filename: str):
    return FileResponse(pdf_directory_path + filename, filename='source.pdf')