class vehicle:
    def __init__(self,vel):
        self.vehi=vel

class car:
    def __init__(self,model):
        self.model=model

    def model_view(self):
        if self.model=="latest":
            return "vehicle needed"
        else:
            return "not needed"
class bikes:
    def __init__(self,bikeid):
        self.bikeid=bikeid
    def bike_view(self):
        if self.bikeid=="latest":
            return "required"
        else:
            return "not required"
        


        
        
           
