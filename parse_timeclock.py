import csv
from datetime import datetime
import sys


def load_data(filename):
	"""
	Loads data from filename into a list of dicts
	"""
	try:
		f = open(filename, 'r')
	except IOError:
		print(filename + ' could not be found!')
		exit(1)

	_list = []
	with f:
		print('Reading ' + filename)
		_reader = csv.reader(f)
		_fieldnames = _reader.next()
		print 'Headers: ', _fieldnames
		_dictreader = csv.DictReader(f, fieldnames = _fieldnames)
		for _row in _dictreader:
			_list.append(_row)

	return _list


def fix_time(data):
	"""
	Parses data to convert timecodes into human-readable times, calculates
	number of minutes spent per operation
	:param data: List of dicts generated by load_data()
	:return: newlist, another list of dicts
	"""
	newlist = []
	for _row in data:
		"""
		<FULLNAME>,<DATEIN>,<TIMEIN>,<DATEOUT>,<TIMEOUT>,<JOBCODE>,<EXPORTSAS>
		Danny Sellers,20141001,0729,20141001,0927,30001,Customer Support
		Danny Sellers,20141001,0927,20141001,0942,5,Break
		"""
		_timein = _row['<TIMEIN>'][:-2], ':', _row['<TIMEIN>'][-2:]
		# converts 0729 to ['07', ':', '29']
		_timeout = _row['<TIMEOUT>'][:-2], ':', _row['<TIMEOUT>'][-2:]
		_newtimein = ''.join(_timein)  # converts _timein to '07:29'
		_newtimeout = ''.join(_timeout)

		_yearin = _row['<DATEIN>'][:4]
		_dayin = _row['<DATEIN>'][4:6]
		_monthin = _row['<DATEIN>'][6:]
		_yearout = _row['<DATEOUT>'][:4]
		_dayout = _row['<DATEOUT>'][4:6]
		_monthout = _row['<DATEOUT>'][6:]

		fmt = '%H:%M'
		_strtimein = datetime.strptime(_newtimein, fmt)
		_strtimeout = datetime.strptime(_newtimeout, fmt)
		_td = _strtimeout - _strtimein  # produces datetime.timedelta, which has diff in seconds

		_timediff = _td.seconds / 60.0  # to minutes

		newlist.append(
			dict(FULLNAME = _row['<FULLNAME>'], JOBCODE = _row['<JOBCODE>'],
				 EXPORTSAS = _row['<EXPORTSAS>'],
				 DAYIN = _dayin, MONTHIN = _monthin, YEARIN = _yearin, DAYOUT = _dayout,
				 MONTHOUT = _monthout, YEAROUT = _yearout, TIMEIN = _newtimein,
				 TIMEOUT = _newtimeout, OPMINS = _timediff))

	return newlist


def parse_people(data):
	peoplelist = []
	# Creates a list of people's names
	for row in data:
		if row['FULLNAME'] not in peoplelist:
			peoplelist.append(row['FULLNAME'])

	# Produce list of dicts containing each person's operation times
	_lst = []
	for person in peoplelist:
		_opdict = {}
		for row in data:
			if row['FULLNAME'] == person:
				_op = row['EXPORTSAS']
				if _op not in _opdict.keys():
					# print('Adding {}'.format(_op))
					_opdict[_op] = row['OPMINS']
				else:
					# print('Seen {}'.format(_op))
					_val = row['OPMINS']
					_opdict[_op] += _val
		_opdict['Total_mins'] = sum(_opdict.values())
		_opdict['Name'] = person

		print('Total mins for {}: {}'.format(_opdict['Name'], _opdict['Total_mins']))
		_lst.append(_opdict)

	return _lst


def write_data(filename, data):
	w = open(filename, 'wb')
	print('Writing to {}'.format(filename))

	assert isinstance(data, list)
	if type(data[0]) != dict:
		with w:
			_writer = csv.writer(w, delimiter=',')
			for row in data:
				_writer.writerow(row)
	else:
		_newfieldnames = data[0].keys()
		with w:
			writer = csv.DictWriter(w, delimiter = ',', lineterminator = '\n',
									fieldnames = _newfieldnames)
			writer.writerow(dict((fn, fn) for fn in _newfieldnames))
			for _row in data:
				writer.writerow(_row)


def pivot_worktime(peoplelist):
	"""
	Creates pivoted table with operation as first column with each
	person's stats filling in rows
	:param peoplelist: list of dicts containing {op: time} pairs
	:return: list of lists (matrix) for writing
	"""

	# First extract a list of operations from people dicts for first column
	oplist = []
	for person in peoplelist:
		for operation in person.keys():
			if operation != 'Name' and operation != 'Total_mins' and operation not in oplist:
				oplist.append(operation)

	timetable = []  # list of rows = matrix
	_namelist = []  # list of peoples' names, to be inserted at position 0
	_persontotals = ['Employee Total']  # list for peoples' total time
	_totaltime = 0.0

	for op in oplist:
		_opsum = 0.0
		_rowlist = [op]  # list to store row starts with the operation name

		for person in peoplelist:
			if person['Name'] not in _namelist:
				_namelist.append(person['Name'])
			if op not in person.keys():
				person[op] = 0.0
			for key, value in person.iteritems():
				if key == op:
					_rowlist.append(value)  # put person's op time value in row
					_opsum += value  # for calculating total time / operation

		timetable.append(_rowlist)
		_rowlist.append(_opsum)  # tack it on the end

	for person in peoplelist:
		_persontime = person['Total_mins']
		_totaltime += _persontime
		if _persontime not in _persontotals:
			_persontotals.append(_persontime)
	_persontotals.append(_totaltime)

	_namelist.insert(0, 'Job Code')
	_namelist.insert(len(_namelist), 'Job Code Total')
	timetable.insert(0, _namelist)
	timetable.insert(len(timetable), _persontotals)

	return timetable


if __name__ == '__main__':
	if len(sys.argv) < 2:
		_filename = raw_input('Input file? (must be .csv format)\t')
	elif len(sys.argv) == 2:
		_filename = sys.argv[1]
	else:
		print("That's too many arguments!")
		sys.exit(1)

	if '.csv' not in _filename:
		_filename += '.csv'

	#_filename = 'Oct14_JobCodes_PDX.csv'
	# _filename = 'sample.csv'

	_data = load_data(_filename)
	_newdata = fix_time(_data)
	_data = parse_people(_newdata)

	_timetable = pivot_worktime(_data)

	_outfile = _filename[:-4] + '_new.csv'
	# write_data(_outfile, _data)  # write un-pivoted dicts
	write_data(_outfile, _timetable)