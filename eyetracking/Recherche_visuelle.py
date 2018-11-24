from eyetracking.eyelink import *

class Recherche_visuelle(Experiment):

    #Center of the screen.
    x_center = 512
    y_center = 384

    # Half of image width
    #image_width = 163
    # Half of image height
    #image_height = 115

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) > 24 and line[8] == "tgt_hor":
            try:
                if len(line) > 24 and line[8] == "tgt_hor":
                    target_hp = int(line[10]) + Recherche_visuelle.x_center
                    target_vp = int(line[15]) + Recherche_visuelle.y_center
                    num_of_dis = int(line[5])
                    cor_resp = int(line[20])
                    response = int(line[24])
                    if target_hp < Recherche_visuelle.x_center:
                        target_side = "L"
                    else:
                        target_side = "R"
                return {
                    'target_hp' : target_hp,
                    'target_vp' : target_vp,
                    'num_of_dis' : num_of_dis,
                    'cor_resp' : cor_resp,
                    'response' : response,
                    'target_side' : target_side
                }
            except:
                pass
        return None

    def isResponse(self, line: List[str]) -> bool :
        return len(line) >= 6 and 'repondu' in line[5]


    #Creates an image scanpath for one trial.
    def scanpath(trial):#,nb_distractors,targetname,target_hp,target_vp,response_time,frame_list,distance_x,distance_y):
        print('scanpath')
        print(trial.features)
        '''
        point_list = []
        nb_points = 0
        color = (1,1,0)

        for line in trial:
            if Eyelink.is_line_recording(line):
                point_list.append([float(line[1]),float(line[2])])
            elif len(line) >= 5 and line[3] == "sujet" and line[4] == "a":
                break
        nb_points = float(len(point_list))

        plt.axis([0,1024,0,768])
        plt.gca().invert_yaxis()
        plt.axis('off')

        #Draws distractors and target frames.
        for i in range(0,len(point_list)-1):
            plot_segment([point_list[i][0],point_list[i+1][0]],[point_list[i][1],point_list[i+1][1]],c=color)
            color = (1, color[1] - 1.0/nb_points , 0)

        if nb_distractors == "1":
            if (target_hp,target_vp) == frame_list[0]:
                plot_target(frame_list[0],cor_resp,(0,0,0),distance_x,distance_y)
                plot_frame(frame_list[5],(0,0,0),distance_x,distance_y)
            else:
                plot_target(frame_list[5],cor_resp,(0,0,0),distance_x,distance_y)
                plot_frame(frame_list[0],(0,0,0),distance_x,distance_y)

        elif nb_distractors == "3":
            for i in range (1,5):
                if (target_hp,target_vp) == frame_list[i]:
                    plot_target(frame_list[i],cor_resp,(0,0,0),distance_x,distance_y)
                else:
                    plot_frame(frame_list[i],(0,0,0),distance_x,distance_y)
        elif nb_distractors == "5":
            for i in range (0,6):
                if (target_hp,target_vp) == frame_list[i]:
                    plot_target(frame_list[i],cor_resp,(0,0,0),distance_x,distance_y)
                else:
                    plot_frame(frame_list[i],(0,0,0),distance_x,distance_y)

        targetname = targetname.replace("jessi\\Images_finales\\","")
        targetname = targetname.replace(".png","")
        response_time = int(response_time)

        plt.text(float(target_hp)-(10*len(targetname)),float(target_vp),targetname)
        plt.text(800,-20,"response_time = " + str(response_time))
        '''
