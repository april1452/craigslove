/* multi bar chart showing word frequency */
var margin = {
		top: 20,
		right: 20,
		bottom: 100,
		left: 60
	},
	width = 1200 - margin.left - margin.right,
	height = 600 - margin.top - margin.bottom,
	frequencyJsonFile = '../data/frequencies.json';

var x0 = d3.scale.ordinal()
	.rangeRoundBands([0, width], .1);

var x1 = d3.scale.ordinal();

var y = d3.scale.linear()
	.range([height, 0]);

var color = d3.scale.category20();

var xAxis = d3.svg.axis()
	.scale(x0)
	.orient("bottom");

var yAxis = d3.svg.axis()
	.scale(y)
	.orient("left")
	.tickFormat(d3.format("2r"));

var draw = function(filepath) {
	var svg = d3.select("#barchart").append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.json(filepath, function(error, json) {
		if (error) throw error;
		var data = json.sort(function(a, b) {
			return b.values[0].value - a.values[0].value;
		});
		var words = data.map(function(d) {
			return d.word;
		});

		var categories = data[0]['values'].map(function(d) {
			return d.category;
		});

		x0.domain(words);
		x1.domain(categories).rangeRoundBands([0, x0.rangeBand()]);
		y.domain([0, d3.max(data, function(d) {
			return d3.max(d.values, function(d) {
				return d.value;
			});
		})]);

		svg.append("g")
			.attr("transform", "translate(0," + height + ")")
			.call(xAxis)
			.selectAll("text")
			.attr("y", 0)
			.attr("x", 9)
			.attr("dy", "1em")
			.attr("transform", "rotate(45)")
			.style("text-anchor", "start");

		svg.append("g")
			.call(yAxis)
			.append("text")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.text("word frequency");

		var word = svg.selectAll(".word")
			.data(data)
			.enter().append("g")
			.attr("class", "word")
			.attr("name", function(d) {
				return d.word;
			})
			.attr("transform", function(d) {
				return "translate(" + x0(d.word) + ",0)";
			});

		var rects = word.selectAll("rect")
			.data(function(d) {
				return d.values;
			})
			.enter().append("rect")
			.attr("width", x1.rangeBand())
			.attr("x", function(d) {
				return x1(d.category);
			})
			.attr("y", function(d) {
				return y(d.value);
			})
			.attr("height", function(d) {
				return height - y(d.value);
			})
			.style("fill", function(d) {
				return color(d.category);
			});

		// rects.on("mouseover", function(d) {
		// 		var word = $(this).parent('.word').attr("name");
		// 		var barwidth = $(this).attr("width");
		// 		var p = $(this).position();
		// 		d3.select('#tooltip').html(tooltipstring(word, d.category, d.value))
		// 			.style("left", p.left - barwidth - ($('#tooltip').width() / 2) + "px")
		// 			.style("top", (p.top - height + 45) + "px")
		// 			.transition().duration(100).style("opacity", 1);
		// 	})
		// 	.on("mouseout", function() {
		// 		d3.select('#tooltip').transition().duration(100).style("opacity", 0);
		// 	});

		var legend = svg.selectAll(".legend")
			.data(categories)
			.enter().append("g")
			.attr("transform", function(d, i) {
				return "translate(0," + i * 20 + ")";
			});

		legend.append("rect")
			.attr("x", width - 18)
			.attr("width", 18)
			.attr("height", 18)
			.style("fill", color);

		legend.append("text")
			.attr("x", width - 24)
			.attr("y", 9)
			.attr("dy", ".35em")
			.style("text-anchor", "end")
			.text(function(d) {
				if (d == 'w4m') {
					return 'woman seeking man';
				}
				if (d == 'w4w') {
					return 'woman seeking woman';
				}
				if (d == 'm4m') {
					return 'man seeking man';
				}
				if (d == 'm4w') {
					return 'man seeking woman';
				}
				return 'strictly platonic';
			});
	});

};

var tooltipstring = function(word, category, value) {
	return '<b>' + category + '</b><br>\"' + word + '\"<br>' + d3.round(value, 2) + '<br>';
}


$(document).ready(function() {
	console.log('ready');
	draw(frequencyJsonFile)
});