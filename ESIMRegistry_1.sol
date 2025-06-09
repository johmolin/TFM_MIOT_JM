// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ESIMRegistry {
    struct Device {
        string eid;
        string iccid;
        string mno;
        address pubkey;
    }

    mapping(string => Device) private devices; // Indexed by EID

    event DeviceRegistered(string eid, string iccid, string mno, address pubkey);
    event OperatorChanged(string eid, string oldIccid, string oldMno, string newIccid, string newMno);

    function registerDevice(string calldata eid, string calldata iccid, string calldata mno, address pubkey) external {
        require(devices[eid].pubkey == address(0), "Device with this EID already registered");

        devices[eid] = Device({
            eid: eid,
            iccid: iccid,
            mno: mno,
            pubkey: pubkey
        });

        emit DeviceRegistered(eid, iccid, mno, pubkey);
    }

    function changeOperator(string calldata eid, string calldata newIccid, string calldata newMno) external {
        require(devices[eid].pubkey != address(0), "Device with this EID not found");
        require(keccak256(bytes(devices[eid].mno)) != keccak256(bytes(newMno)), "Device already has this operator");

        string memory oldIccid = devices[eid].iccid;
        string memory oldMno = devices[eid].mno;

        devices[eid].iccid = newIccid;
        devices[eid].mno = newMno;

        emit OperatorChanged(eid, oldIccid, oldMno, newIccid, newMno);
    }

    function getDevicePubKey(string calldata eid) external view returns (address) {
        require(devices[eid].pubkey != address(0), "Device not found");
        return devices[eid].pubkey;
    }

    function getDeviceData(string calldata eid) external view returns (string memory, string memory, address) {
        require(devices[eid].pubkey != address(0), "Device not found");
        return (devices[eid].iccid, devices[eid].mno, devices[eid].pubkey);
    }
}
