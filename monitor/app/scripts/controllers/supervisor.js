'use strict';

angular.module('poligloMonitorApp')
  .controller('SupervisorStatusCtrl', function($scope, Supervisor) {
    $scope.getStatus = function(){
      Supervisor.status(function(data){
        $scope.data = data;
      });
    };
    $scope.stopProcess = function(processName){
      Supervisor.stopProcess(processName, function(data){
        $scope.getStatus();
      })
    };
    $scope.startProcess = function(processName){
      Supervisor.startProcess(processName, function(data){
        $scope.getStatus();
      })
    };
    $scope.getStatus();
  });
