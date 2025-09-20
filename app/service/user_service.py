from typing import Any, Dict, List, Optional
from app.db.firebase import db
from app.models.user import UserRegister, UserRegisterInput, UserRole
from firebase_admin import auth

def create_user(user_data: UserRegister | UserRegisterInput):
    try:
        role = getattr(user_data, "role", UserRole.EMPLOYEE)
        doc_ref = db.collection("users").document(user_data.uid)

        doc_ref.set({
            "name": user_data.name,
            "birthday": user_data.birthday,
            "imageUrl": user_data.imageUrl,
            "role": role.value,
            "level": "1",
            "globalPoints": "0",
            "monthlyPoints": "0"
        }, merge=True)

        return {"message": "User data saved successfully", "uid": user_data.uid, "role": str(role)}
    except Exception as e:
        return {"error": str(e)}


def get_user_by_email(email):
    try:
        user = auth.get_user_by_email(email)
        return {"uid": user.uid, "email": user.email}
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        return {"error": str(e)}

def forgot_password(email):
    try:
        link = auth.generate_password_reset_link(email)
        return {"message": "Password reset link generated", "link": link}
    except auth.UserNotFoundError:
        return {"error": "Email not found"}
    except Exception as e:
        return {"error": str(e)}

def user_by_id(uid):
    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            
            level_id = user_data.get("level")
            if level_id:
                level_ref = db.collection('levels').document(level_id)
                level_doc = level_ref.get()
                
                if level_doc.exists:
                    level_data = level_doc.to_dict()
                    user_data['level'] = {
                        'id': level_id,
                        'name': level_data.get("name")
                    }
            
            return user_data
        else:
            return {"error": "User not found"}
    except Exception as e:
        return {"error": str(e)}

def delete_user(uid):
    try:
        user_ref = db.collection('users').document(uid)
        user_ref.delete()
        return {"message": "User deleted successfully"}
    except Exception as e:
        return {"error": str(e)}

def ranking():
    try:
        user_ref = db.collection('users')
        users = user_ref.stream()
        user_data = sorted(
            [
                {
                    "name": user.get("name"),
                    "imageUrl": user.get("imageUrl"),
                    "monthlyPoints": int(user.get("monthlyPoints"))
                }
                for user in users
            ],
            key=lambda x: x["monthlyPoints"],
            reverse=True
        )

        return user_data
    except Exception as e:
        return {"error": str(e)}

def rewards(level_id):
    try:
        level_ref = db.collection('levels').document(level_id)
        level_doc = level_ref.get()
        
        if level_doc.exists:   
            level_data = level_doc.to_dict()
            rewards_ids = level_data.get("rewards", "").split(", ")
            
            rewards_list = []
            for reward_id in rewards_ids:
                reward_ref = db.collection('rewards').document(reward_id)
                reward_doc = reward_ref.get()
                
                if reward_doc.exists:
                    rewards_list.append(reward_doc.to_dict())
            
            return rewards_list
        else:
            return {"error": "Level not found"}
    except Exception as e:
        return {"error": str(e)}

def level(level_id):
    try:
        level_ref = db.collection('levels').document(level_id)
        level_doc = level_ref.get()
        
        if level_doc.exists:
            level_data = level_doc.to_dict()
            return level_data
        else:
            return {"error": "Level not found"}
    except Exception as e:
        return {"error": str(e)}

def check_level(uid):
    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            
            
            current_level = int(user_data.get("level", "1"))
            current_global_points = int(user_data.get("globalPoints", "0"))
            
            next_level_ref = db.collection("levels").document(str(current_level + 1)).get()
            
            if next_level_ref.exists:
                next_level_data = next_level_ref.to_dict()
                next_level_points_required = int(next_level_data['points'])
                
                if current_global_points >= next_level_points_required:
                    new_level = current_level + 1
                    user_ref.update({"level": str(new_level)})
                    user_data["level"] = str(new_level)
                    user_data["level_updated"] = True
                else:
                    user_data["level_updated"] = False
                
            return user_data
        else:
            return {"error": "User not found"}
    except Exception as e:
        return {"error": str(e)}

def get_top_level_status(level_id):
    try:
        levels_ref = db.collection('levels').stream()
        
        levels_list = []
        for level in levels_ref:
            level_data = level.to_dict()
            level_data['id'] = level.id
            levels_list.append(int(level_data['id']))
        print(levels_list)
        if not levels_list or (int(level_id) not in levels_list):
            return {"error": "No levels found or levels have invalid IDs."}
        
        max_level_id = max(levels_list)
        
        return {"isTopLevel": int(level_id) == max_level_id}
    
    except ValueError:
        return {"error": "Invalid level ID format, unable to convert to integer."}
    except Exception as e:
        return {"error": str(e)}

def reset_monthly_points():
    users_ref = db.collection("users").stream()
    updated_users_count = 0

    for user in users_ref:
        user_ref = db.collection("users").document(user.id)
        user_ref.update({"monthlyPoints": "0"})
        updated_users_count += 1 

    return f"Monthly points reset for {updated_users_count} users."

def _get_assigned_shift_for_employee(uid: str) -> Optional[Dict[str, Any]]:

    try:
        q = (
            db.collection("shift_assignments")
              .where("id_employee", "==", uid)
              .limit(1)
              .get()
        )
        if not q:
            return None

        sa = q[0].to_dict() or {}
        shift_id = sa.get("id_shift")
        if not shift_id:
            return None

        shift_doc = db.collection("shifts").document(shift_id).get()
        if not shift_doc.exists:
            return {"id": shift_id, "name": None, "start_time": None, "end_time": None}

        s = shift_doc.to_dict() or {}
        return {
            "id": shift_id,
            "name": s.get("name"),
            "start_time": s.get("start_time"),
            "end_time": s.get("end_time"),
        }
    except Exception:
        return None

def list_employees_with_shift_service() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    
    docs = db.collection("users").where("role", "==", "EMPLOYEE").stream()
    for d in docs:
        data = d.to_dict() or {}
        uid = data.get("uid") or d.id
        name = data.get("name") or "EMPLOYEE"

        shift = _get_assigned_shift_for_employee(uid)

        out.append({
            "uid": uid,
            "name": name,
            "role": "EMPLOYEE",
            "shift": shift,
        })
    return out