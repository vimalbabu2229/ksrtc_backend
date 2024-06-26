from datetime import time
import pandas as pd 
import datetime

# Crew Scheduler
class ScheduleCrew:
    def __init__(self, conductors, drivers) -> None:
        self.conductors = list(conductors)
        self.drivers = list(drivers)
        
    def get_crew(self):
        conductor = None
        driver = None
        if len(self.conductors) > 0:
            conductor = self.conductors.pop()

        if len(self.drivers) > 0:
            driver = self.drivers.pop()

        return (conductor, driver)

# Vehicle Scheduler 
class ScheduleVehicles:
    def __init__(self, vehicles) -> None:
        # vehicles : (vehicle_id, end time)
        # Initially the busy part is set to 00:00:00
        self.vehicles = [[vehicle, time(0, 0, 0)] for vehicle in list(vehicles)]
        self.vehicle_count = len(self.vehicles)
      
    def get_vehicle(self, start_time, end_time):
        
        if self.vehicle_count > 0:
            # check if the end time of last vehicle is less than start_time
            if self.vehicles[-1][1] < start_time :
                vehicle = self.vehicles.pop()
                vehicle[1] = end_time
                self.vehicles.insert(0, vehicle)
                return vehicle[0]
            else:
                # Iterate through the self.vehicles to find any vehicle with end_time 
                # less than the start_time of this schedule
                for vehicle in self.vehicles:
                    if vehicle[1] < start_time:
                        vehicle[1] = end_time
                        return vehicle[0]
                return None     
        else :
             return None

# Trip processor to preprocess trips data before scheduling 
class TripPreprocessor:
    def __init__(self):
        self.df = pd.DataFrame()

    # Function to convert time to seconds
    @staticmethod
    def time_to_seconds(time_obj):
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    # Function to convert seconds to human-readable time format
    @staticmethod
    def seconds_to_time(df, columns):
        df[columns] = df[columns].apply(lambda x: pd.to_datetime(x, unit='s').dt.strftime('%H:%M:%S'))

    def preprocess_data(self, input_df):
        
        self.df = input_df

        if not all(self.df.columns):
            return None

        self.df = self.df.dropna().drop_duplicates()
        time_columns = ['departure_time', 'arrival_time', 'running_time']
        for col in time_columns:
            self.df[col] = pd.to_datetime(self.df[col], format='%H:%M:%S', errors='coerce').dt.time
            self.df[col] = self.df[col].apply(self.time_to_seconds)

        # Convert other columns to appropriate data types
        for col in self.df.columns:
            if col not in time_columns:  # Exclude time columns
                self.df[col] = self.df[col].convert_dtypes()

        # Sort the DataFrame by 'Departure Time' column
        sorted_df = self.df.sort_values('departure_time', ascending=True).reset_index(drop=True)
        
        return sorted_df

    def preprocess(self, trips):
        # convert trips in list of dict to df  
        input_df = pd.DataFrame(trips)
        preprocessed_df = self.preprocess_data(input_df)
        if preprocessed_df is not None:
            return preprocessed_df
        else:
            return pd.DataFrame()

# Trip Scheduler 
class ScheduleTrips:
    def __init__(self, start_leg='PSL') -> None:
        self.START_PLACE = start_leg
        self.df = pd.DataFrame()
        #start_legs contain the legs with departure place as start_place
        self.start_legs = pd.DataFrame()
        # MIN_DUTY = 27000 #setting the minimum duty as 7:00 hrs 
        self.MIN_DUTY = 7 * 3600 #setting the minimum duty as 7:00 hrs + 15min sign in  and 15 min sign out = 07:30 hrs
        # The ideal duty is 7:30 hrs with a 15 min break at the start and end . Then total 8:00 
        # MAX_DUTY = 30600 # setting the maximum duty as 8:30 hrs
        self.MAX_DUTY = 9 * 3600  # setting the maximum duty as 09:00 hrs + 15min sign in  and 15 min sign out = 09:30 hrs
        self.MAX_SPREAD_OVER = 43200 # setting maximum spread over to 12 hrs 
        self.MIN_TERMINAL_GAP = 300
        self.MAX_TERMINAL_GAP = 900
        self.BREAK = 1800 # break time of 30 min to avoid 5hrs continuous working
        self.IS_BREAK = False # setting the break status as false by default 
        self.MAX_SPLIT = 3600 # Setting the maximum split time as 60 min 
        self.MIN_TEMPSET_SIZE = 2 # define the minimum number of legs in a temp_set
        self.BREAK_LIMIT_DUTY = 18000 # 5hrs of continuous duty  
        self.MIN_LIMIT_DUTY = 12600 # After 3.5 hrs of duty we can try entering the 30 min break

        # FOR THE PURPOSE OF MEASURING THE PERFORMANCE 
        success = 0 # Not necessary , just to count the number of start legs taken 
        trips_count = 0 # count the number of trips 
        exe_generateTempSet  = 0
        exe_popTempSet  = 0
        
    # function to covert seconds to time object 
    def secToTime(self, seconds):
        if seconds:
            hrs, rem = divmod(seconds, 3600)
            mint, sec = divmod(rem , 60)
            return datetime.time(hour=hrs, minute=mint, second= sec)
        else :
            return seconds

    # #### Generate Tempset 
    # - Below function creates the temset for a particular leg in the stack . It checks for the needed criteria and then creates the set of legs that are possibly gives us a feasible solution 
    def generateTempSet(self, leg, mode = 0) -> pd.DataFrame:
        # mode 0 means normal trips and mode 1 means consider 30 min break also
        # FN LOGIC IS NOT CORRECT , NEED TO CREATE THE TEMP SET ONLY WITH THE CRITERIA
        # SORTING THEM AFTER CREATING THE ENTIRE TEMPSET IS NOT OPTIMAL

        # Creating a copy of the main legs.Can be limited with steering duty remaining 
        temp_set_df = self.df[(self.df['departure_place'] == leg['arrival_place'])
                    & (self.df['departure_time'] > leg['arrival_time'])]
        temp_set_df = temp_set_df.sort_values(
            'departure_time', ascending=True).reset_index(drop=True)
        temp_set_df['terminal_gap'] = temp_set_df['departure_time'] - leg['arrival_time']
        # Sorting and resetting index
        # '''BELOW LINE MAY BE NOT NECESSARY'''
        # display(temp_set)
        temp_set = pd.DataFrame()
        # THERE ARE CHANCES THAT THE TEMP SET MAY BE EMPTY , SO WE ARE TRYING FOR 
        #  THE NEXT LEVEL SEARCHING
        if mode == 0:
            min_terminal_gap = self.MIN_TERMINAL_GAP
            terminal_gap = self.MAX_TERMINAL_GAP
            ADD_ON = 900 # 15 min
        else :
            min_terminal_gap = self.BREAK
            terminal_gap = self.BREAK + self.MAX_TERMINAL_GAP
            ADD_ON = 900 # 15 min
        # NEED TO OPTIMIZE BELOW LOOP AS EVERY TIME IT LOOPS THROUGH THE ENTIRE LEGS TILL
        # THE SPECIFIED TERMINAL GAP , CAN USE EXTEND OR CONCAT TO ITERATIVELY ADDING UP THE 
        # TEMP SET  
        while len(temp_set) < self.MIN_TEMPSET_SIZE and terminal_gap < self.MAX_SPLIT: # 1 hr split
            temp_set = temp_set_df[
                (temp_set_df['terminal_gap'] >= min_terminal_gap) & (
                    temp_set_df['terminal_gap'] < terminal_gap)  # |
                # (temp_set['Duty'] >= MIN_DUTY) & (temp_set['Duty'] <= MAX_DUTY)
            ]
            terminal_gap += ADD_ON
        # print(f"Type of gap = {type(temp_set['Terminal Gap'][0])}")
        # temp_set['Duty'] = leg['Duty'] + temp_set['Running Time'] + temp_set['Terminal Gap']
        temp_set.loc[:, 'duty'] = leg['duty'] + temp_set['running_time'] # should bee run for all legs
        # temp_set.loc[temp_set['Terminal Gap'] < MAX_TERMINAL_GAP, 'Duty'] += temp_set.loc[temp_set['Terminal Gap'] < MAX_TERMINAL_GAP, 'Terminal Gap']
        mask = temp_set['terminal_gap'] < self.MAX_TERMINAL_GAP
        temp_set.loc[mask, 'duty'] += temp_set.loc[mask, 'terminal_gap']
        # if len(temp_set) < 2 : print(f"Size of tempset == {len(temp_set)}")
        temp_set.reset_index(drop=True, inplace=True)
        return temp_set

    #  Pop Tempset 
    # - This function pops the currently visited leg from the corresponding tempset, then the tempset will always contain the possible legs from a given leg that satisfies the criteria needed   
    def popTempSet(self, temp_set) -> pd.DataFrame:
        # global exe_popTempSet
        temp_set.drop(0, inplace=True)
        # print("popTempSet")
        # display(temp_set)
        temp_set.reset_index(inplace=True)
        temp_set.drop('index',axis= 1, inplace=True)
        # exe_popTempSet += (y - x)
        return temp_set

    ## Display Trip
    def displayTrip(self, stack):
        # global trips_count
        frame = pd.DataFrame()
        for x in stack:
            frame = pd.concat([frame, (x['current_leg'].to_frame()).T], ignore_index=True)
        frame['terminal_gap'] = frame['terminal_gap'].shift(-1)
        #Calculating the steering duty 
        duty = self.secToTime(frame['duty'].iloc[len(frame) - 1])
        spread_over = self.secToTime((stack[-1]['current_leg'])['arrival_time'] - (stack[0]['current_leg'])['departure_time'])
        frame = frame.drop('duty', axis=1)
        # trips_count += 1
        return [frame, duty, spread_over]

    # Function to convert seconds to time for entire column
    def seconds_to_time(self, df, columns):
        df[columns] = df[columns].apply(lambda x: pd.to_datetime(x, unit='s').dt.strftime('%H:%M:%S'))

    #Remove Legs
    # - Once a leg is taken for a trip , it should be removed so that it will not be considered for the next round of iterations  
    def removeLegs(self, trip) -> int:
        success = 0
        if not trip.empty:
            for index, row in trip.iterrows():
                sl_no = row['id']
                # Remove from df
                self.df.drop(self.df[self.df['id'] == sl_no].index, axis=0, inplace=True)
                # Remove from start_legs if Departure Place is START_PLACE
                if row['departure_place'] == self.START_PLACE:
                    self.start_legs.drop(self.start_legs[self.start_legs['id'] == sl_no].index, axis=0, inplace=True)
                    success += 1
            self.df.reset_index(drop=True, inplace=True)
            self.start_legs.reset_index(drop=True, inplace=True)
        return success

    #Backtracking 
    def backtrack(self, stack):
        #  If temp_set is empty , it means that we cannot go to any other places from the 
        # last leg , so we can pop the last leg in the stack  
        stack.pop()
        # After popping stack top , there are also chances that the temp_set of top elements 
        # in the stack may be empty, so those ones also should be popped out, because we cannot 
        # goto anywhere else from there  
        while(stack[-1]['temp_set'].empty) :
                stack.pop()
        stack[-1]['current_leg'] = stack[-1]['temp_set'].iloc[0]
        stack[-1]['temp_set'] = self.popTempSet(stack[-1]['temp_set'])

    # Decorators 
    def exception_handler(self, func):
        def wrapper(stack):
            try:
                return func(stack)
            except Exception as e:
                # removeLegs(start_leg)
                self.start_legs.drop(0, axis=0, inplace=True)
                self.start_legs.reset_index(drop=True, inplace=True)
                # print(f"Error occured = {e}")
                return False
        return wrapper

    # ALGORITHM
    def generateTrip(self, stack):
        try:    
            # Making the break flag False initially 
            # SHOULD BE CONSIDERED GLOBALLY 
            IS_BREAK = False
            spread_over = 0
            
            while len(stack) > 0 :
                temp_set = self.generateTempSet(stack[-1]['current_leg'])
                if temp_set.empty :
                    # EXCEPTION CASES CAN BE HANDLED HERE , MEANS WE CAN CHECK WHETHER THE 
                    # STACK GETS EMPTY ON BACKTRACKING TO AVOID OUT OF BOUND 
                    self.backtrack(stack)
                    # After backtracking a new leg is replaced on the top , so we can just continue
                    continue
                
                if (stack[-1]['current_leg'])['duty'] > self.MIN_LIMIT_DUTY and stack[-1]["break"] == False:
                    # display(stack[-1])
                    temp_set = self.generateTempSet(stack[-1]['current_leg'], 1)
                    # temp_set.reset_index(drop=True, inplace=True)
                    # print("TempSet is below ")
                    # display(temp_set)
                    stack.append({"current_leg": temp_set.iloc[0], "temp_set": self.popTempSet(temp_set), "break": True})
                    spread_over = (stack[-1]['current_leg'])['arrival_time'] - (stack[0]['current_leg'])['departure_time']
                else:
                    # In the below line , break is made to follow the stack top because after setting it true inside the 
                    # break insertion logic , the subsequent legs should have break True . So it should follow stack top  
                    stack.append({"current_leg": temp_set.iloc[0], "temp_set": self.popTempSet(temp_set), "break": stack[-1]["break"]})
                    spread_over = (stack[-1]['current_leg'])['arrival_time'] - (stack[0]['current_leg'])['departure_time']
                if (stack[-1]['current_leg'])['duty'] > self.MAX_DUTY or spread_over > self.MAX_SPREAD_OVER \
                    or ((stack[-1]['current_leg'])['duty'] > self.BREAK_LIMIT_DUTY and stack[-1]["break"] == False) :
                    self.backtrack(stack)
                else:
                    if (top_leg:=stack[-1]['current_leg'])['arrival_place']==self.START_PLACE and top_leg['duty'] > self.MIN_DUTY \
                    and stack[-1]["break"]==True: 
                        # break
                        return stack
        except Exception as e:
                # removeLegs(start_leg)
                self.start_legs.drop(0, axis=0, inplace=True)
                self.start_legs.reset_index(drop=True, inplace=True)
                # print(f"Error occured = {e}")
                return False

    ## MAIN PART
    def schedule(self, trips): # Gets trips as list dict from database 
        # create preprocessor instance 
        if not trips:
            return [] # Return empty list, if trips is empty
        
        preprocessor = TripPreprocessor()
        preprocessed_df = preprocessor.preprocess(trips)
        if preprocessed_df.empty:
            return [] # If preprocessed df is empty then return empty list 
        # Initializations
        self.df = preprocessed_df.reset_index(drop=True)
        self.df['terminal_gap'] = [0] * len(self.df)
        self.df['duty'] = [0] * len(self.df)
        self.start_legs = self.df[self.df['departure_place'] == self.START_PLACE].sort_values('departure_time', ascending=True)
        self.start_legs.reset_index(drop=True,inplace=True)
        # setting the initial running time of start legs as its running time itself
        self.start_legs['duty'] = self.start_legs['running_time']  
        schedules = []  # List to store each schedule
        trip_number = 1  # Initialize trip number
        if not self.start_legs.empty:
            while not self.start_legs.empty:
                status = self.generateTrip([{"current_leg": self.start_legs.iloc[0], "temp_set": pd.DataFrame(), "break": False}])
                if status:
                    result = self.displayTrip(status)
                    self.removeLegs(result[0])
                    # Append JSON representation of trip to the list
                    # schedule = result[0].to_dict(orient='records')
                    schedule = result[0]
                    trips = [(index, trip['id'], str(self.secToTime(trip['terminal_gap']))) for index, trip in schedule.iterrows()]
                    schedules.append({
                        "schedule_number": trip_number,  # Include trip number in JSON
                        "start_time":str(self.secToTime(schedule.iloc[0]['departure_time'])),
                        "end_time":str(self.secToTime(schedule.iloc[len(schedule)-1]['arrival_time'])),
                        "steering_duty": str(result[1]),  # Convert steering duty to string for JSON serialization
                        "spread_over": str(result[2]),     # Convert spread over to string for JSON serialization
                        "trips": trips,
                    })
                    trip_number += 1  # Increment trip number
                else:
                    continue

        return schedules
