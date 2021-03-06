import json
import os
import filetype
import cv2
import uuid
from django.conf import settings
from django.http import HttpResponse
from PIL import Image as PILImage
from rest_framework import serializers
from api.helpers import test_image

from main.models import User

from .models import Image, ImageFile
from projects.models import Projects


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    class Meta:
        model = User
        fields = ('id','email','password','full_name','user_type','image')
        read_only_fields = ('id','user_type')

    def create(self, validated_data):
        user = User.objects.create(email=validated_data['email'],
                                full_name=validated_data['full_name'])
        if(validated_data.get('image')):
            user.image = validated_data.get('image')
        user.set_password(validated_data['password'])
        user.save()
        return user

class ImageFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageFile
        fields = ('file','tested','result','score','object_type','verified')

class ImageSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField(read_only=True)
    user_type = serializers.SerializerMethodField(read_only=True)
    project_name = serializers.SerializerMethodField(read_only=True)
    image_files = ImageFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Image
        fields = ('id','url','title','description','lat','lng','user_id','user_name','user_type','project_id','project_name','image_files','created_at','updated_at')
        read_only_fields = ('user_name','user_type','created_at', 'updated_at','project_name')

    def get_user_name(self, image):
        return image.user.full_name if image.user else None
    
    def get_user_type(self, image):
        return image.user.user_type if image.user else None
    
    def get_project_name(self, image):
        return image.project.project_name if image.project else None

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        image_files = self.context.get('view').request.FILES

        if len(image_files) > 0 and len(image_files) < 8: # Images count 1 to 7
            image = Image.objects.create(title=validated_data.get('title'),
                                        description=validated_data.get('description'),
                                        lat=validated_data.get('lat'),
                                        lng=validated_data.get('lng'),
                                        user_id=user.id,
                                        project_id=validated_data.get('project_id', None))
            
            project = None
            if validated_data.get('project_id', None):
                project = Projects.objects.filter(id=validated_data.get('project_id')).get()
            if not project:
                image.delete()
                error = {'message': 'Invalid Project'}
                raise serializers.ValidationError(error)

            e = 0 # Check if files uploaded or Not
            u = 0 # Uploaded Count
            for image_file in image_files.values():
                try:
                    img = PILImage.open(image_file)
                    img.verify()
                    image_obj = ImageFile.objects.create(image=image, file=image_file)
                    offline = False
                    detect_model = project.detect_model

                    try:
                        if project.offline_model and project.offline_model.file:
                            offline = True
                            detect_model = project.offline_model
                    except:
                        offline = False

                    ################
                    ### RUN TEST ###
                    ################
                    test_image(image_obj, validated_data.get('title'), validated_data.get('description'), detect_model=detect_model, project=project.unique_name(), offline=offline)

                    u = u + 1
                except Exception as err:
                    print(err)
                    print('File Failed to Upload - NOT AN IMAGE')
                    e = e + 1
            
            if(u >= 1): # At least one uploaded good to go
                ###############################
                ##### IF FINE TO CONTINUE #####
                ###############################
                return image
            else: # No Files Upload Throw error
                image.delete()
                error = {'message': str(e)+' Files failed to Upload. (Probably, Files are not type Image)'}
                raise serializers.ValidationError(error)
        else:
            error = {'message': 'No Images provided or too much (>7) images provided.'}
            raise serializers.ValidationError(error)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.lat = validated_data.get('lat', instance.lat)
        instance.lng = validated_data.get('lng', instance.lng)
        instance.project_id = validated_data.get('project_id', instance.project_id)
        
        image_files = self.context.get('view').request.FILES

        project = None
        if validated_data.get('project_id', None):
            project = Projects.objects.filter(id=validated_data.get('project_id')).get()
        if not project:
            error = {'message': 'Invalid Project'}
            raise serializers.ValidationError(error)
        
        if len(image_files) < 8:
            e = 0 # Check if files uploaded or Not
            u = 0 # Uploaded Count
            for image_file in image_files.values():
                try:
                    img = PILImage.open(image_file)
                    img.verify()
                    image_obj = ImageFile.objects.create(image=instance, file=image_file)
                    offline = False
                    detect_model = project.detect_model

                    try:
                        if project.offline_model and project.offline_model.file:
                            offline = True
                            detect_model = project.offline_model
                    except:
                        offline = False
                    
                    ################
                    ### RUN TEST ###
                    ################
                    test_image(image_obj, validated_data.get('title'), validated_data.get('description'), detect_model=detect_model, project=project.unique_name(), offline=offline)
                    u = u + 1
                except Exception as err:
                    print(err)
                    print('File Failed to Upload - NOT AN IMAGE')
                    e = e + 1
            
            if(u >= 1): # At least one uploaded good to go
                instance.save()
                return instance
            else: # No Files Upload Throw error
                instance.save()
                error = {'message': str(e)+' Files failed to Upload. (Probably, Files are not type Image)'}
                raise serializers.ValidationError(error)
        else:
            error = {'message': 'Too much (>7) images provided.'}
            raise serializers.ValidationError(error)

###################################
# CREATE AND STORE VIDEO TO FRAMES:
###################################
class VideoFrameSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField(read_only=True)
    user_type = serializers.SerializerMethodField(read_only=True)
    project_name = serializers.SerializerMethodField(read_only=True)
    image_files = ImageFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Image
        fields = ('id','url','title','description','lat','lng','user_id','user_name','user_type','project_id','project_name','image_files','created_at','updated_at')
        read_only_fields = ('user_name','user_type','created_at', 'updated_at', 'project_name')

    def get_user_name(self, image):
        return image.user.full_name if image.user else None
    
    def get_user_type(self, image):
        return image.user.user_type if image.user else None

    def get_project_name(self, image):
        return image.project.project_name if image.project else None

    # Function to get the frame image, save to image_file model and test it via ai model
    def getFrame(self, vidcap, count, sec, image_model, project=None):
        vidcap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
        hasFrames,image = vidcap.read()
        if hasFrames:
            filename = '{}.{}'.format(uuid.uuid4().hex, 'jpg')
            saveto = os.path.join('media/image/', filename)
            saveto = None
            if not os.path.exists(os.path.join('media/image/')):
                saveto = os.environ.get('PROJECT_FOLDER','') + '/media/image/'+filename
            else:
                saveto = os.path.join('media/image/', filename)

            cv2.imwrite(saveto, image) # save frame as JPG file
            image_obj = ImageFile.objects.create(image=image_model, file=str(os.path.join('media/image/', filename)).replace('media/',''))
            offline = False
            detect_model = project.detect_model

            try:
                if project.offline_model and project.offline_model.file:
                    offline = True
                    detect_model = project.offline_model
            except:
                offline = False
            
            ################
            ### RUN TEST ###
            ################
            test = test_image(image_obj, image_model.title, image_model.description, detect_model=detect_model, project=project.unique_name(), offline=offline)
        return hasFrames

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        video_files = self.context.get('view').request.FILES

        # If videos exists on upload store Image model to db
        if len(video_files) > 0 and len(video_files) < 8: # Video count 1 to 7
            image = Image.objects.create(title=validated_data.get('title'),
                                        description=(validated_data.get('description')+' - (Via Video Upload)'),
                                        lat=validated_data.get('lat'),
                                        lng=validated_data.get('lng'),
                                        user_id=user.id,
                                        project_id=validated_data.get('project_id', None))

            project = None
            if validated_data.get('project_id', None):
                project = Projects.objects.filter(id=validated_data.get('project_id')).get()
            if not project:
                image.delete()
                error = {'message': 'Invalid Project'}
                raise serializers.ValidationError(error)

            e = 0 # Check if files uploaded or Not
            u = 0 # Uploaded Count
            count = 1 # Frame generation count
            for video_file in video_files.values():
                saveto = None
                try:
                    # Trying the guess the file type (to verify video)
                    kind = filetype.guess(video_file)
                    filename = None

                    if kind is None:
                        print('Cannot guess file type of video (assuming mp4 just cause, 50% video are kind less with this package)!')
                        filename = '{}.{}'.format(uuid.uuid4().hex, 'mp4')
                    else:
                        print('File extension: %s' % kind.extension)
                        if(kind.extension in ['mp4','mkv','flv','m4v','webm','mov','avi','wmv','mpg']):
                            # Save the video to temp folder
                            filename = '{}.{}'.format(uuid.uuid4().hex, kind.extension)
                        else:
                            print('Not Valid file video extension as filetype check in array of extension.')
                            e = e + 1
                            continue

                    if filename:
                        saveto = os.path.join('media/temp/', filename)
                        saveto = None
                        if not os.path.exists(os.path.join('media/temp/')):
                            saveto = os.environ.get('PROJECT_FOLDER','') + '/media/temp/'+filename
                        else:
                            saveto = os.path.join('media/temp/', filename)
                            
                        fout = open(saveto, 'wb+')
                        # Iterate through the chunks and write to the file
                        for chunk in video_file.chunks():
                            fout.write(chunk)
                        fout.close()
                        print(filename)
                        # To Capture the frames use cv2
                        vidcap = cv2.VideoCapture(saveto)
                        sec = 0
                        frameRate = 2 # it will capture image in each 2 second
                        success = self.getFrame(vidcap,count,sec,image,project) # Get frame self function made above
                        while success:
                            if count >= 10: ###### Max 10 images from one video ######
                                break
                            count = count + 1
                            sec = sec + frameRate
                            sec = round(sec, 2)
                            success = self.getFrame(vidcap,count,sec,image,project) # Get frame self function made above

                        u = u + 1
                        # Destroy/Close Video and remove from temp
                        cv2.destroyAllWindows()
                        vidcap.release()
                        os.remove(saveto)
                    else:
                        e = e + 1
                except Exception as err:
                    print(err)
                    print('File Failed to Upload - Something went wrong while processing image.')
                    e = e + 1
            
            if(u >= 1 or count > 1): # At least one uploaded good to go
                ###############################
                ##### IF FINE TO CONTINUE #####
                ###############################
                return image
            else: # No Files Upload Throw error
                image.delete()
                error = {'message': str(e)+' Files failed to Upload. (Probably, Files are not type Video or something much worse)'}
                raise serializers.ValidationError(error)
        else:
            error = {'message': 'No Video provided or too much (>7) video provided.'}
            raise serializers.ValidationError(error)