
angular.module('app', [
	'ui.bootstrap',
	'code-editor',
])
.controller('AppController', function ($scope, $http) {

	$scope.data = { inputText: '', results: { json: '', yaml: '', sentences: [] } };
	$scope.settings = { ssplit: true };
	$scope.active = 0;

	var themelist = ace.require('ace/ext/themelist');
	$scope.themes = themelist.themes;
	$scope.settings.theme = themelist.themesByName['textmate'];
	$scope.settings.wrap = false;
	$scope.parsing = false;
	$scope.selectedSentence = undefined;

	$scope.selectSentence = function (sentence) {
		$scope.selectedSentence = sentence;
	};

	$scope.downloadJSON = function () {
		saveAs(new Blob([$scope.data.results.json], {type: "application/json;charset=utf-8"}), 'results.json');
	};

	$scope.downloadYAML = function () {
		saveAs(new Blob([$scope.data.results.yaml], {type: "text/yaml;charset=utf-8"}), 'results.yaml');
	};
	
	$scope.parse = function () {

		$scope.parsing = true;
		// $http.post('/api/parse', $scope.data.inputText, { headers: { 'Content-Type': 'text/plain' } }).then(function (response) {
		$http({
			method: 'POST',
			url: '/api/parse'+($scope.settings.ssplit?'?ssplit=true':''),
			headers: {
				'Content-Type': 'text/plain'
			},
			data: $scope.data.inputText
		}).then(function (response) {
			// console.log(response.data);
			// console.log(jsyaml.dump(response.data));
			$scope.data.results.sentences = response.data;
			$scope.data.results.json = angular.toJson(response.data, true);
			// fix: convert AMR tabs to spaces (for YAML)
			for(let sentence of response.data) {
				sentence.AMRtext = sentence.AMRtext.replace(/\t/g, '    ');
			}
			$scope.data.results.yaml = jsyaml.dump(response.data, { flowLevel: 3, sortKeys: true });
			// if($scope.data.results.sentences.length > 0) $scope.selectedSentence = $scope.data.results.sentences[0];
			$scope.selectedSentence = undefined;
			$scope.active = 1;
			$scope.parsing = false;
		}, function (response) {
			console.error(response.data);
			$scope.parsing = false;
		});
	};

	$scope.loadText = function (event) {
		var reader, file;
		for(var i=0; i<event.dataTransfer.files.length; ++i) {
			file = event.dataTransfer.files[i];
			reader = new FileReader();

            reader.onload = function (file) {
                var data = this.result;
                if(file.name.match(/\.amr/i)) {
					var m, sentences = [];
					data = data.split('\n');
					for(let line of data) {
						m = line.match(/^#.*::snt (.+?)(?: ::\w+ .*)?$/);
						if(m)
							sentences.push(m[1]);
					}
					$scope.settings.ssplit = false;
					$scope.data.inputText = sentences.join('\n');
                } else {
					$scope.data.inputText = data;
                }
				$scope.$apply();
            }.bind(reader, file);

            // reader.onloadend = function () {
            // };

			reader.readAsText(file);
		}
	};

})
.directive('dropFile', function ($parse, $timeout) {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {

			function dragEnterLeave(event) {
				event.stopPropagation();
				event.preventDefault();
				element.removeClass('drag-over');
			}

			element[0].addEventListener('dragenter', dragEnterLeave);
			element[0].addEventListener('dragleave', dragEnterLeave);
			element[0].addEventListener('dragover', function (event) {
				element.addClass('drag-over');
			});
			element[0].addEventListener('drop', function (event) {
				dragEnterLeave(event);
				scope.$eval(attrs.dropFile)(event);
			});
		}
	};
})
.directive('spin', function () {
    return {
        restrict: 'E',
        replace: true,
        require: '?ngModel',
        transclude: true,
        template: '<div class="spin"></div>',
        link: function (scope, element, attrs, ngModel) {

            var opts = {
                lines: 13, // The number of lines to draw
                length: 5, // The length of each line
                width: 2, // The line thickness
                radius: 3, // The radius of the inner circle
                corners: 1, // Corner roundness (0..1)
                rotate: 0, // The rotation offset
                direction: 1, // 1: clockwise, -1: counterclockwise
                color: '#000', // #rgb or #rrggbb
                speed: 1, // Rounds per second
                trail: 60, // Afterglow percentage
                shadow: false, // Whether to render a shadow
                hwaccel: true, // Whether to use hardware acceleration
                className: 'spinner', // The CSS class to assign to the spinner
                zIndex: 2e9, // The z-index (defaults to 2000000000)
                top: 'auto', // Top position relative to parent in px
                left: 'auto' // Left position relative to parent in px
            };

            // override options
            angular.extend(opts, scope.$eval(attrs.options));

            var spinner = new Spinner(opts);
            if(!ngModel)
            {
                spinner.spin(element[0]);
                return;
            }

            scope.$watch(attrs.ngModel, function (value) {
                if(value)
                    spinner.spin(element[0]);
                else
                    spinner.stop();
			});
		}
	};
})
;
