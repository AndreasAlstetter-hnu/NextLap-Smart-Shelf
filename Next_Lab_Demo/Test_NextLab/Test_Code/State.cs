public enum State
{
    Idle,

    // AMR -> WH
    Request_AMR_Drive_PlacementPosition,
    Response_AMR_Arrived_PlacementPosition,

    // WH -> AMR
    Request_QR10_Place_WH,
    Response_QR10_Placed_WH,

    // AMR -> SCARA
    Request_AMR_Drive_SCARA_Position,
    Response_AMR_Arrived_SCARA_Position,

    // FEET PLACEMENT
    Request_SCARA_Place_Feet_Balanced_White,
    Request_SCARA_Place_Feet_Balanced_Yellow,
    Request_SCARA_Place_Feet_Balanced_Orange,
    Request_SCARA_Place_Feet_Balanced_Red,
    Request_SCARA_Place_Feet_Balanced_Green,
    Request_SCARA_Place_Feet_Balanced_Blue,
    Request_SCARA_Place_Feet_Balanced_Brown,
    Request_SCARA_Place_Feet_Balanced_Black,
    Request_SCARA_Place_Feet_Lightweight_White,
    Request_SCARA_Place_Feet_Lightweight_Yellow,
    Request_SCARA_Place_Feet_Lightweight_Orange,
    Request_SCARA_Place_Feet_Lightweight_Red,
    Request_SCARA_Place_Feet_Lightweight_Green,
    Request_SCARA_Place_Feet_Lightweight_Blue,
    Request_SCARA_Place_Feet_Lightweight_Brown,
    Request_SCARA_Place_Feet_Lightweight_Black,
    Request_SCARA_Place_Feet_Spartan_White,
    Request_SCARA_Place_Feet_Spartan_Yellow,
    Request_SCARA_Place_Feet_Spartan_Orange,
    Request_SCARA_Place_Feet_Spartan_Red,
    Request_SCARA_Place_Feet_Spartan_Green,
    Request_SCARA_Place_Feet_Spartan_Blue,
    Request_SCARA_Place_Feet_Spartan_Brown,
    Request_SCARA_Place_Feet_Spartan_Black,
    Response_SCARA_Feet_Placed,

    // AMR -> NEXTLAP
    Request_AMR_Drive_NextLap_Position,
    Response_AMR_Arrived_NextLap_Position,

    // PLATE
    Request_Pick_Plate_Lightweight_White,
    Request_Pick_Plate_Lightweight_Blue,
    Request_Pick_Plate_Lightweight_Black,
    Request_Pick_Plate_Balanced_White,
    Request_Pick_Plate_Balanced_Blue,
    Request_Pick_Plate_Balanced_Black,
    Request_Pick_Plate_Spartan_White,
    Request_Pick_Plate_Spartan_Blue,
    Request_Pick_Plate_Spartan_Black,
    Response_Plate_Picked,

    Request_Place_Plate,
    Response_Plate_Placed,

    // CASE
    Request_Pick_Case_White,
    Request_Pick_Case_Yellow,
    Request_Pick_Case_Orange,
    Request_Pick_Case_Red,
    Request_Pick_Case_Green,
    Request_Pick_Case_Blue,
    Request_Pick_Case_Brown,
    Request_Pick_Case_Black,
    Response_Case_Picked,

    Request_Place_Case,
    Response_Case_Placed,    

    // BATTERY
    Request_Pick_Battery,
    Response_Battery_Picked, 

    Request_Place_Battery,
    Response_Battery_Placed,

    // BATTERY CABLE
    Request_Pick_Battery_Cable,
    Response_Battery_Cable_Picked, 

    Request_Place_Battery_Cable,
    Response_Battery_Cable_Placed,

    // ENGINE 1
    Request_Pick_Engine1,
    Response_Engine1_Picked,

    Request_Place_Engine1,
    Response_Engine1_Placed,

    // ENGINE 2
    Request_Pick_Engine2,
    Response_Engine2_Picked,

    Request_Place_Engine2,
    Response_Engine2_Placed,

    // ENGINE 3
    Request_Pick_Engine3,
    Response_Engine3_Picked,

    Request_Place_Engine3,
    Response_Engine3_Placed,

    // ENGINE 4
    Request_Pick_Engine4,
    Response_Engine4_Picked,

    Request_Place_Engine4,
    Response_Engine4_Placed,

    // RFID TAG
    Request_Pick_RFID_Tag,
    Response_RFID_Tag_Picked,

    Request_Place_RFID_Tag,
    Response_RFID_Tag_Placed,

    // RECEIVER
    Request_Pick_Receiver,
    Response_Receiver_Picked,

    Request_Place_Receiver,
    Response_Receiver_Placed,

    // RECEIVER CABLE
    Request_Pick_Receiver_Cable,
    Response_Receiver_Cable_Picked,

    Request_Place_Receiver_Cable,
    Response_Receiver_Cable_Placed,

    // RIVETS
    Request_Pick_Rivets,
    Response_Rivets_Picked,

    Request_Place_Rivets,
    Response_Rivets_Placed,

    // CONTROLLER
    Request_Pick_Controller,
    Response_Controller_Picked,

    Request_Place_Controller,
    Response_Controller_Placed
}