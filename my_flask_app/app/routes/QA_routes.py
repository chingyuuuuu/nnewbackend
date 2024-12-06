from flask import Blueprint, request, jsonify,send_from_directory,session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import os
import requests
from ..config import Config


QA_routes=Blueprint('QA_routes',__name__)

@QA_routes.route('/savedata',methods=['POST'])
def save_data():
     from ..models import QA
     from ..import db

     # 獲得當前文件的目錄
     current_dir = os.path.dirname(os.path.abspath(__file__))
     #絕對路徑-上一級目錄當中
     uploads_folder = os.path.join(current_dir,'..', 'uploads')

     if not os.path.exists(uploads_folder):
         os.makedirs(uploads_folder)

     image_url=None
     if 'image' in request.files:
         image_file = request.files['image']
         # 圖片儲存在絕對路徑，但是資料庫儲存的是相對路徑
         image_path = os.path.join("uploads", image_file.filename)
         absolute_image_path = os.path.join(uploads_folder, image_file.filename)
         image_file.save(absolute_image_path)  # 保存文件到指定路径
         image_url = f"http://127.0.0.1:5000/{image_path.replace(os.sep, '/')}"

     data = request.form
     question = data.get('question')
     answer = data.get('answer')
     userId = data.get('user_id')
     type=data.get('type',None)#如果有就儲存沒有就none


     if not question or not answer:
              return jsonify({"error":"question and answer are required"}),400

     try:
             #創建QA
             new_qa=QA(
                  type=type,
                  question=question,
                  answer=answer,
                  image=image_url ,
                  quser_id=userId
             )
             db.session.add(new_qa)
             db.session.commit()

             return jsonify({"message":"Data saved successfully"}),200
     except Exception as e:
              print(f"Error occured:{e}")
              return jsonify({"error":"An error occurred while saving"}),500


@QA_routes.route('/getqa',methods=['GET'])#用userid去查找已經創建的qa
def getqa():
    from ..models import QA
    try:
        user_id=request.args.get('user_id')#從http中獲取QA，前端有用參數傳入就好
        if not user_id:
            return jsonify({"error":"user_id is not found"}),400

        qa_list=QA.query.filter_by(quser_id=user_id).all()
        if not qa_list:
            return jsonify([]),200
        result=[]
        for qa in qa_list:
            result.append({
                  'qaId':qa.QA_id,
                  'question':qa.question,
                  'answer':qa.answer
            })
        return jsonify(result),200
    except Exception as e:
         print(f"Error occurred:{e}")
         return jsonify({"error": "An error occurred while fetching QA data"}), 500


@QA_routes.route('/getqabyqaid/<int:qaId>', methods=['GET'])
def getqabyqaid(qaId):
    from ..models import QA
    try:

        qa = QA.query.filter_by(QA_id=qaId).first()

        if not qa:
            return jsonify([]), 200

        image_url = None
        if qa.image:

            if not qa.image.startswith('http://') and not qa.image.startswith('https://'):
                image_url = f"http://127.0.0.1:5000/{qa.image}"
            else:
                image_url = qa.image

        result = [{
            'qaId': qa.QA_id,
            'question': qa.question,
            'answer': qa.answer,
            'type': qa.type if qa.type else None,
            'image': image_url
        }]

        return jsonify(result), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while fetching QA data"}), 500

@QA_routes.route('/updatedata/<int:qaId>',methods=['POST'])
def update(qaId):
    from ..models import QA
    from ..import db
    try:
        data=request.get_json()#獲取前端提交的數據
        qa=QA.query.filter_by(QA_id=qaId).first()
        if not qa:
            return jsonify({"error":"QA not found"}),404
        #更新資料
        qa.question=data.get('question',qa.question)
        qa.answer=data.get('answer',qa.answer)
        qa.type=data.get('type',qa.type)
        qa.image=data.get('image',qa.image)
        db.session.commit()
        return jsonify({"message":"QA updated successfully"}),200
    except Exception as e:
        print(f"Error occured:{e}")
        return jsonify({"error":"An error occurred while updating QA"}),500


@QA_routes.route('/deletedata/<int:qaId>', methods=['DELETE'])
def delete_data(qaId):
    from ..models import QA
    from .. import db
    try:
        qa = QA.query.get(qaId)

        if qa:
            db.session.delete(qa)
            db.session.commit()
            return jsonify({"message": "Data deleted successfully"}), 200
        else:
            return jsonify({"error": "Data not found"}), 404

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while deleting"}), 500


@QA_routes.route('/uploads/<filename>',methods=['GET'])
def uploaded_file(filename):
    uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    return send_from_directory(uploads_folder, filename)




#儲存未解答的問題
def save_unanswered_question(question,userId):
    from ..models import db,UnansweredQuestions
    from datetime import datetime,timezone

    existing_question=UnansweredQuestions.query.filter_by(question=question,fk_user_id=userId).first()
    #如果問題已經存在
    if existing_question:
        existing_question. occurence_count+=1
        existing_question.updated_at=datetime.now(timezone.utc),
    else:
        new_question=UnansweredQuestions(
            question=question,
            occurence_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            fk_user_id=userId,
        )
        db.session.add(new_question)
    db.session.commit()

#預設基本的問候語
greeting_responses={
     "你好":"你好!有甚麼可以幫助您的?",
     "謝謝":"不客氣，隨時為您服務!",
     "再見":"再見!期待再次為您服務",
}

#從前端獲得問題->然後尋找相似的問題->獲取答案
@QA_routes.route('/query_qa',methods=['POST'])
def query_qa():
    from ..models import QA

    #接收用戶問題
    user_question=request.json.get('question')
    userId=request.json.get('user_id')
    if not user_question:
        return jsonify({"error":"Question is required"}),400

    #Step1-查詢基本問後語
    for greeting,response in greeting_responses.items():
        if greeting in user_question:
            return jsonify({"answer": response}),200

    #Step2-從資料庫中獲取所有問答
    qa_data=QA.query.all()
    questions=[qa.question for qa in qa_data]

    #使用TfidfVectorizer進行向量化-將文本轉換成數值化的向量表，以便進行數學運算
    vectorizer=TfidfVectorizer(tokenizer=jieba.lcut)
    question_vectors=vectorizer.fit_transform(questions)
    user_vector=vectorizer.transform([user_question])

    #計算相似度
    similarities=cosine_similarity(user_vector,question_vectors)
    most_similar_idx=similarities.argmax()

    # 若相似度高於某個閾值，則認為資料庫中有匹配答案
    if similarities[0][most_similar_idx] > 0.5:  # 0.5 可根據需求調整
        best_answer = qa_data[most_similar_idx].answer
        return jsonify({"answer": best_answer}), 200
    else:
        return jsonify({"answer": "抱歉，目前無法回答您這個問題"}), 200
    #Step4-若無法找到匹配答案，調用Hugging face API去做回答,這個1分鐘只能回答一次
    """
        try:
        save_unanswered_question(user_question,userId)
        answer = query_huggingface_api(user_question)
        return jsonify({"answer":answer}),200
    except Exception as e:
        print(f"Error occured:{e}")
        return jsonify({"error":"An error occurred while processing the question"}),500
    
def  query_huggingface_api(question):
    url=Config.HF_API_URL
    headers={"Authorization":f"Bearer {Config.HF_API_TOKEN}"}
    data = {"inputs": question}
    response = requests.post(url,headers=headers,json=data)
    #處理回應
    if response.status_code==200:
        response_json = response.json()
        if isinstance(response_json,list) and len(response_json)>0:
            return response_json[0]["generated_text"].strip()
        else:
            return "抱歉，無法產生回應"
    else:
        raise Exception(f"Hugging Face API Error: {response.status_code} - {response.text}")
    """



#加載未回答的問題
@QA_routes.route('/unanswered_questions', methods=['GET'])
def fetch_unanswered_questions():
    from ..models import UnansweredQuestions
    user_id = request.args.get('user_id')
    try:
        unanswered_questions = UnansweredQuestions.query.filter_by(fk_user_id=user_id).all()
        result = [
            {
                "id": question.id,
                "question": question.question,
                "occurence_count": question.occurence_count,
            }
            for question in unanswered_questions
        ]

        return jsonify(result), 200

    except Exception as e:
        print(f"Error fetching unanswered questions: {e}")
        return jsonify({"error": "Failed to fetch unanswered questions"}), 500







