% Class Gripper_interface provides Matlab API to which controls the Robotiq
% F2-85 gripper with TCP/IP protocal

% Copyright (c) 2025 Annie Huang, Jiacheng Li. All rights reserved. 

classdef Gripper_Interface < handle
    properties (Access = private)
        gripper
        ip = '172.22.22.2';     % default IP
        port = 63352;           % default port
        AutoInit = 1;           % will establish connection when instantiate
        warn = 1;
    end
    
    % GET&SET Reference
    %   ACT - activate (1 = activated)
    %   GTO - go to (will perform go to with the actions set)
    %   FOR - force (0-255)
    %   SPE - speed (0-255)
    %   POS - position (0-255), 0 = open

    %   ATR - auto-release (emergency slow move, cannot get value, deactivate after set to 1)
    %   STA - status (0 = is reset, 1 = activating, 3 = active)
    %   PRE - position request (echo of last commanded position)
    %   OBJ - object detection (0 = moving, 1 = stuck when openning, 2 = stuck when closing, 3 = no object at rest)

    methods
        % Constructor
        function obj = Gripper_Interface(ip, port, AutoInit)
            if nargin > 0
                obj.ip = ip;
            end
            if nargin > 1
                obj.port = port;
            end
            if nargin >2
                obj.AutoInit = AutoInit;
            end

            if obj.AutoInit
                connect(obj)
                obj.SET("POS", 0);
                activate(obj)
            else
                obj.warn = 0;  % this would suppress warnings.
            end
        
        end

        function connect(obj)
            obj.gripper = tcpclient(obj.ip, obj.port, 'Timeout', 5);
            pause(0.2); 
        end

        function disconnect(obj)
            clear obj.gripper;
        end

        function final_pos = grip(obj, blockFlag)
            if nargin < 2
                blockFlag = 1;
            end
            final_pos = move(obj, 255, 0, 0, blockFlag);
        end

        function final_pos = release(obj, blockFlag)
            if nargin < 2
                blockFlag = 1;
            end
            final_pos = move(obj, 0, 0, 0, blockFlag);
        end

        function pos = get_pos(obj) % might needed
            pos = obj.GET("POS");
        end

        %% Advanced
        function SET(obj, var, val)
            cmd = sprintf("SET %s %d\n", var, val);
            write(obj.gripper, cmd, "string");
            pause(0.05);
        end

        function val = GET(obj, var)
            cmd = sprintf("GET %s\n", var);
            write(obj.gripper, cmd, "string");
            pause(0.05);
            response = readline(obj.gripper);
            tokens = split(strtrim(response));
            if ~contains(tokens{1}, var)
                error("Unexpected response: %s", response);
            end
            val = str2double(tokens{2});
        end

        function reset(obj)
            obj.SET("ACT", 0);
            while obj.GET("ACT") ~= 0 || obj.GET("STA") ~= 0
                obj.SET("ACT", 0);
                pause(0.1);
            end
            pause(0.5);
        end

        function activate(obj)
            disp("Activating Gripper");
            if obj.GET("STA") ~= 3
                obj.reset();
                while obj.GET("ACT") ~= 0 || obj.GET("STA") ~= 0
                    pause(0.1);
                end
                obj.SET("ACT", 1);
                pause(1.0); % take some time to be in activating status
                while obj.GET("ACT") ~= 1 || obj.GET("STA") ~= 3
                    pause(0.1);
                end
                pause(0.5);
            end
        end

        function final_pos = move(obj, position, speed, force, blockFlag)
            if (nargin > 2) 
                speed = min(max(speed, 0), 255);
                obj.SET("SPE", speed);
                if obj.warn && (speed~=0)
                    warning("Gripper Speed Set, please confirm");
                end
            end

            if (nargin > 3)
                force = min(max(force, 0), 255);
                obj.SET("FOR", force);
                if obj.warn &&(force~=0)
                    warning("Gripper Force Set, please confirm");
                end
            end

            if nargin < 5
                blockFlag = 1;
            end

            position = min(max(position, 0), 255);

            
            obj.SET("POS", position);
            obj.SET("GTO", 1);

            % Confirm the CMD is received.
            while obj.GET("PRE") ~= position
                pause(0.01);
            end

            if blockFlag    % wait till stop by default
                obj_status = obj.GET("OBJ");
                while obj_status == 0
                    obj_status = obj.GET("OBJ");
                    pause(0.01);
                end
            end

            final_pos = obj.GET("POS");
        end
    end
end
