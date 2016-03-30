"use strict";


// url of current javascript file, from: http://stackoverflow.com/a/2255727
// var scripts = document.getElementsByTagName("script"), src = scripts[scripts.length-1].src;

angular.module('code-editor', []).directive('codeEditor', function ($parse, $timeout) {
	return {
		restrict: 'E',
		transclude: true,
		replace: true,
		require: '?ngModel',
		template: '<div></div>',
		link: function (scope, element, attrs, ngModel) {

			var editor = ace.edit(element[0]);

			// default
			editor.getSession().setUseWrapMode($parse(attrs.wrap));

			// themelist, but should include ace-builds/src/ext-themelist.js
			// console.log(ace.require('ace/ext/themelist'));

			var themeListenerRemove;
			// var modeListenerRemove;

			var defaultTheme = "ace/theme/monokai";
			var defaultMode = "ace/mode/python";

			attrs.$observe('theme', function (attrValue) {
				if(themeListenerRemove)
					themeListenerRemove();

				themeListenerRemove = undefined;

				if(attrValue)
					themeListenerRemove = scope.$watch(attrValue, function (value) {
						if(value)
							editor.setTheme("ace/theme/"+value)
						else
							editor.setTheme(defaultTheme);
					});
				else
					editor.setTheme(defaultTheme);
			});

			attrs.$observe('mode', function (value) {
				if(value)
					editor.getSession().setMode("ace/mode/" + value);
				else
					editor.getSession().setMode(defaultMode);
			});

			attrs.$observe('readonly', function (value) {
				editor.setReadOnly(value);
				// editor.setReadOnly(scope.$eval(attrs.readOnly));
			});

			// editor.setTheme("ace/theme/monokai");
			// editor.getSession().setMode("ace/mode/python");

			var skip = false;

			scope.$watch(attrs.ngModel, function (value) {

				if(skip)
					return;

				editor.getSession().getDocument().setValue(value);
			});

			scope.$watch(attrs.wrap, function (value) {
				if(value !== undefined)
					editor.getSession().setUseWrapMode(value);
			});

			scope.$watch(attrs.show, function (value) {
				if(value) {
					$timeout(function () {
						editor.resize(true);
					}, 0);
				}
			});
			
			// editor.on('change', function (e) {
			// 	console.log('change:', editor.getSession().getDocument().getValue());
			// 	if(!ngModel)
			// 		return;
			// 	scope.$apply(function () {
			// 		$parse(attrs.ngModel).assign(scope, editor.getSession().toString());
			// 	});
			// });
			
			editor.on('blur', function (e) {

				// console.log('blur:', editor.getSession().getDocument().getValue());

				if(!ngModel)
					return;

				// https://groups.google.com/forum/?fromgroups=#!searchin/angular/directive$20two$20binding$20parent$20without$20isolate/angular/p6TkKUmXOhA/ToqD2lK3bawJ
				// https://groups.google.com/forum/#!topic/angular/yI-iMUFBU6s/discussion
				// http://docs.angularjs.org/api/ng.$parse
				skip = true;
				scope.$apply(function () {
					$parse(attrs.ngModel).assign(scope, editor.getSession().getDocument().getValue());
				});
				skip = false;
			});
		}
	};
});
